# python imports
from itertools import groupby
from random import randint
from typing import TypeVar, Iterable, Any, Dict, List
from struct import pack

# third-party imports
from elftools.elf.sections import Section

#project imports
from .base import HashPatchSectionBase

## The @ref IncrementalIntegrity `Self` type
SelfType = TypeVar('SelfType', bound='IncrementalIntegrityBase')


## Represents an incremental integrity check.
#  The seed value for this check is taken from the result of the previous hash. It should be supplied
#  by the developer; this value is not written into the binary to prevent trivial mapping. The first
#  check is seeded by a random value injected using the INTEGRITY_SEED definition.
#  For incremental integrity checks it is important that each check can only be performed once (without
#  re-entering the first item in the sequence) else checks will be thrown off balance. Multiple sequences
#  can be defined for extra fun.
class IncrementalIntegrityBase(HashPatchSectionBase):


    ## Creates a new instance of the @ref IncrementalIntegrity object.
    #  @param self the instance of the object that is invoking this method.
    #  @param section the section this descriptor was built from.
    #  @param start_address start of region that contains the integrity hash generation.
    #  @param end_address end of the region that contains the integrity hash generation.
    #  @param sequence the name of the sequence that this check belongs to.
    #  @param order the order of the check in the sequence (numbers do not have to be consecutive, or unique).
    def __init__(self, section:Section, start_address:int, end_address:int, sequence:str, order:int) -> SelfType:
        super().__init__(section, start_address, end_address)
        self.sequence = sequence
        self.order = order


    ## Given a list of sections, extracts those that describe incremental integrity checks and returns them 
    #    as a map; the key of the map is the name of a sequence/chain, and the value is a list of descriptors
    #    associated with the named chain.
    #  @param cls the type of class that is invoking this method.
    #  @param sections a list of sections to build the map from.
    #  @returns Map keyed with the sequence name, and assocaited to a list of descriptors that form that chain.
    @classmethod
    def group_integrity_checks(cls, sections:List) -> Dict[str, List[SelfType]]:
        
        cls.Log.debug(f"discovering incremental integrity chains...")

        unprocessed_chains = {}
        
        for section in sections:
            if isinstance(section, IncrementalIntegrityBase):
                if not section.sequence in unprocessed_chains:
                    cls.Log.debug(f"discovered new incremental integrity chain '{section.sequence}'.")
                    unprocessed_chains[section.sequence] = [ section ]
                else:
                    unprocessed_chains[section.sequence].append(section)

        cls.Log.debug(f"found {len(unprocessed_chains)} incremental integrity chains.")

        return unprocessed_chains




## The @ref ChainLayer `Self` type
ChainLayerType = TypeVar('ChainLayerType', bound='IncrementalIntegrityLayer')

class IncrementalIntegrityLayer(object):

    def __init__(self) -> ChainLayerType:
        self.murmur_seed  = None
        self.murmur_out = None
        self.entry_points = []
        self.xor_to_known = []
        self.insert_hash  = []



## The @ref IncrementalIntegrityChain `Self` type
ChainSelfType = TypeVar('ChainSelfType', bound='IncrementalIntegrityChain')

## Incremental integrity chain
#  An incremental integrity chain are a series of binary integrity checks that are inter-dependant. The concept 
#  is that the result from one hash iteration is used to seed the next. In this way you can take a hash at one 
#  point, but not bother to check it - only checking the state at the end of the process. If the binary was ever
#  modified in memory during a check (even if its been restored at the final check), the value will be incorrect.
#  This can help making tracking down exactly where things went awry more problematic.
class IncrementalIntegrityChain(list[IncrementalIntegrityLayer]):


    ## Creates a new instance of the @ref IncrementalIntegrityChain object.
    #  @param self the instance of the object that is invoking this method.
    #  @param name the name of the sequence this chain defines.
    def __init__(self, name) -> ChainSelfType:
        self.name = name

    ## Adds a new layer to the integrity chain.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the newly created layer
    def add_layer(self) -> IncrementalIntegrityLayer:
        new_layer = IncrementalIntegrityLayer()
        self.append(new_layer)
        return new_layer
    
    ## Checks that the integrity chain is configured properly.
    #  There are various things you can do wrong with a chain; this tries to stop you making those mistakes.
    #  @param self the instance of the object that is invoking this method.
    def validate(self) -> None:
        
        if not self: # this really shouldn't ever happen
            raise RuntimeError(f"Incremental integrity chain '{self.name}' has no components - how did this happen?")

        for index, layer in enumerate(self):

            if not layer.entry_points:
                # this occurs when REQUIRES_INTEGRITY_XOR_TO_KNOWN or REQUIRES_INTEGRITY_MURMUR_HASH is used on a layer that doesn't exist.
                # It doesn't make sense to do this - these check must be on a defined layer where we know the hash (does a check between layers mean use hash N-1 or N+1)?
                raise RuntimeError(f"Layer #{index} of incremental integrity chain '{self.name}' contains no active integrity elements - did you REQUIRES_INTEGRITY_XOR_TO_KNOWN on a unique layer?")

            if index == 0:
                for hash_recalculation in layer.entry_points: 
                    # only root layers should have seeds. It must have a seed to make it unique - make sure the developer placed one.
                    if not list(hash_recalculation.integrity_seed_offsets()):
                        raise RuntimeError(f"Incremental integrity chain '{self.name}' contains root described in '{hash_recalculation.section.name}'; this code is expected to inject an INTEGRITY_SEED but this wasn't seen.")
            else: # index != 0
                for hash_recalculation in layer.entry_points:
                    if list(hash_recalculation.integrity_seed_offsets()):
                        raise RuntimeError(f"Incremental integrity chain '{self.name}' contains successive layer described in '{hash_recalculation.section.name}'; this code is not expected to inject an INTEGRITY_SEED as this value should be sourced from a previous layer.")


