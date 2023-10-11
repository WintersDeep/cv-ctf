# python imports
from itertools import groupby
from random import randint
from typing import TypeVar, Iterable, Any, Dict, List
from struct import pack

# third-party imports
from elftools.elf.sections import Section

#project imports
from ebp.common.algorithm import MurmurOaat64
from .incremental_integrity_base import IncrementalIntegrityBase, IncrementalIntegrityChain
from .xor_to_known_value import XorToKnownValue
from .insert_murmur import InsertMurmur

## The @ref IncrementalIntegrity `Self` type
SelfType = TypeVar('SelfType', bound='IncrementalIntegrity')


## Represents an incremental integrity check.
#  The seed value for this check is taken from the result of the previous hash. It should be supplied
#  by the developer; this value is not written into the binary to prevent trivial mapping. The first
#  check is seeded by a random value injected using the INTEGRITY_SEED definition.
#  For incremental integrity checks it is important that each check can only be performed once (without
#  re-entering the first item in the sequence) else checks will be thrown off balance. Multiple sequences
#  can be defined for extra fun.
class IncrementalIntegrity(IncrementalIntegrityBase):


    ## Configures and validates intial state information needed for patching.
    #  @param cls the type of class that is invoking this method.
    #  @param sections a list of sections that can be used during initialisation.
    #  @returns the state of the initialisation process on success or None if initialisation did not occur / no processing required.
    @classmethod
    def configure_non_volatile(cls, sections:List) -> Any:
        
        chain_map = {}

        for chain_name, section_list in cls.group_integrity_checks(sections).items():
            
            cls.Log.debug(f"finalising integrity chain '{chain_name}'...")

            use_order = lambda section: section.order
            
            chain = IncrementalIntegrityChain(chain_name)
            ordered_sections = sorted(section_list, key=use_order)

            for _, descriptors in groupby(ordered_sections, use_order):
                
                layer = chain.add_layer()

                for descriptor in descriptors:
                    if   isinstance(descriptor,IncrementalIntegrity):   layer.entry_points.append(descriptor)
                    elif isinstance(descriptor,XorToKnownValue):        layer.xor_to_known.append(descriptor)
                    elif isinstance(descriptor,InsertMurmur):           layer.insert_hash.append(descriptor)
                    else: cls.Log.warning(f"Unknown incremental integrity component located in {descriptor.section.name}.")
            
            chain.validate()

            cls.Log.info(f"Finished configuring incremental integrity chain '{chain.name}' - {len(section_list)} components on {len(chain)} layers.")
            
            chain_map[chain.name] = chain
            
        return chain_map
            


    ## Patches aspects of the binary described by this section entry that can be safely incorprated into the hashing process.
    #  These changes will change the hash of the binary but we are able to accomdate that instability (e.g. the hash seed... we know and fix it in the hash process).
    #  @param cls the type of class that is invoking this method.
    #  @param state the state that was generated and should be applied to the binary,
    @classmethod
    def patch_non_volatile(cls, state:Any) -> None:
        
        for chain in state.values():

            # every chain should have a root layer, and this is the only layer that 
            # has a hard-coded intialisation seed.
            root_layer = chain[0] 

            # record the initial seed and inject it into the code
            root_layer.murmur_seed = randint(0, 0xffffffffffffffff)
            chain_seed_bytes = pack("<Q", root_layer.murmur_seed)            
            cls.Log.debug(f"generated random seed to initialise chain '{chain.name}': 0x{root_layer.murmur_seed:016x}")

            for hash_recalulation in root_layer.entry_points:
                for offset in hash_recalulation.integrity_seed_offsets():
                    cls.Log.debug(f"> patching chain '{chain.name}' root at 0x{offset:016x} ({hash_recalulation.section.name})")
                    hash_recalulation.elf.write(offset, chain_seed_bytes)


    ## Configures and validates intial state information needed for patching volatile aspects of the binary.
    #  @param cls the type of class that is invoking this method.
    #  @param sections a list of sections that can be used during initialisation.
    #  @param state the state generated for the non-volatile patch process
    #  @returns the state of the initialisation process on success or None if this section doesn't action anything volatile.
    @classmethod
    def configure_volatile(cls, sections:List, non_volatile_state:Any) -> Any:
        
        volatile_qwords = sections.volatile_offsets()

        for chain in non_volatile_state.values():

            layer_iterator = chain.__iter__()

            root_layer = next(layer_iterator)
            root_layer.murmur_out = root_layer.entry_points[0].calculate_murmuroaat64(root_layer.murmur_seed, volatile_qwords)

            for previous_layer, layer in enumerate(layer_iterator):  

                layer.murmur_seed = chain[previous_layer].murmur_out
                layer.murmur_out = layer.entry_points[0].calculate_murmuroaat64(layer.murmur_seed, volatile_qwords)

        return non_volatile_state


    ## Patches aspects of the binary described by this section entry that are dependant on the hashing process.
    #  These changes will not change the hash of the binary but do depend on its output (typically using or checking the hash). Note that the scope of 
    #  a volatile QWORD is usually a value, not an operation (i.e. in CMP RAX, 0x1122334455667788 you can change what you are looking for - the imm32 but not the operation).
    #  @param cls the type of class that is invoking this method.
    #  @param state the state that was generated and should be applied to the binary,
    @classmethod
    def patch_volatile(cls, state:Any) -> None:
        
        for chain in state.values():

            for index, layer in enumerate(chain):

                murmur_bytes = pack("<Q", layer.murmur_out)

                for hash_recalculation in layer.entry_points:
                    for offset in hash_recalculation.integrity_hash_offsets():
                        cls.Log.debug(f"> patching integrity hash for chain '{chain.name}' layer #{index} at 0x{offset:016x} ({hash_recalculation.section.name})")
                        hash_recalculation.elf.write(offset, murmur_bytes)

                for xor_to_known in layer.xor_to_known:
                    mask = xor_to_known.known_value ^ layer.murmur_out
                    mask_bytes = pack("<Q", mask)
                    for offset in xor_to_known.xor_mask_offsets():
                        cls.Log.debug(f"> injecting XOR mask for chain '{chain.name}' layer #{index} at 0x{offset:016x} ({xor_to_known.section.name})")
                        xor_to_known.elf.write(offset, mask_bytes)

                for insert_hash in layer.insert_hash:
                    murmur = MurmurOaat64(layer.murmur_out)
                    murmur.consume(insert_hash.expected_value)
                    hash_bytes = pack("<Q", int(murmur))
                    for offset in insert_hash.hash_offsets():
                        cls.Log.debug(f"> injecting murmur hash for known value in chain '{chain.name}' layer #{index} at 0x{offset:016x} ({insert_hash.section.name})")
                        xor_to_known.elf.write(offset, hash_bytes)