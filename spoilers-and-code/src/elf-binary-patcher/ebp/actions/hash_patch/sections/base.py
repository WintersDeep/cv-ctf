# python3 imports
from abc import ABC, abstractclassmethod
from typing import Iterator, TypeVar, Iterable, Any, List, Tuple
from logging import getLogger
from struct import pack, calcsize

# third-party imports
from pwnlib.elf import ELF
from elftools.elf.sections import Section

# project imports
from ebp.common.algorithm import MurmurOaat64


## The @ref HashPatchSectionBase `Self` type
SelfType = TypeVar('SelfType', bound='HashPatchSectionBase')


## Base class for hash related section entries
#  A hash section maybe a bit misleading. Its an entry in the section table that describes something that contributes to, or relies on 
#  the binary integrity mechanism. It might be a location that a hash is taken/generated, it might be the hash generator itself, it
#  might be something that inspects or uses the current hash.
class HashPatchSectionBase(ABC):


    ## Struct description of a DWORD-LE (int / 4 bytes)
    DWORD = "<I"

    ## Struct description of a QWORD-LE (long / 8 bytes)
    QWORD = "<Q"

    ## The size of the @ref DWORD object - calculated rather than set as a fail safe.
    SIZE_OF_DWORD = calcsize(DWORD)

    ## The size of the @ref DWORD object - calculated rather than set as a fail safe.
    SIZE_OF_QWORD = calcsize(QWORD)

    ### The hash value that should be used as a place holder for the current integrity seed.
    #   Locations that this magic number are encountered are generally omitted from integrity checking (hard to have the hash in the thing you are checking).
    #   @remarks defined in C by "integrity.h" as INTEGRITY_HASH
    INTEGRITY_HASH = pack("<Q", 0xaddf00dc0ffeebed)

    ### The hash value that should be used as a place holder for the current integrity seed.
    #   Value used to seed the generator. Note that in some context this might be sensative (for incremental checks this will be the previous hash result),
    #   so always carefully consider if this value should be injected before using it in C code.
    #   @remarks defined in C by "integrity.h" as INTEGRITY_SEED
    INTEGRITY_SEED = pack("<Q", 0x1eaf5adca75f00d5)

    ## Logger used by this class instance.
    #  declared at class scope as its often used by classmethod's.
    Log = getLogger("ebp.action.hash-patch")


    ## Creates a new instance of the @ref HashPatchSectionBase object.
    #  @param self the instance of the object that is invoking this method.
    #  @param section the section this descriptor was built from.
    #  @param start_address start of region that contains the integrity hash generation.
    #  @param end_address end of the region that contains the integrity hash generation.
    def __init__(self, section:Section, start_address:int, end_address:int) -> SelfType:
        self.section = section
        self.start_address = start_address
        self.end_address = end_address
    

    ## Gets the ELF file this deescriptor is part of.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the ELF file this section was created from.
    @property
    def elf(self) -> ELF:
        return self.section.elffile


    ## Reads the memory that is scoped by this patch section.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the bytes in the memory that are in patch scope.
    def scoped_memory(self) -> bytearray:
        memory_size = self.end_address - self.start_address
        return self.elf.read(self.start_address, memory_size)


    ## Returns an enumerator of all occurances of the given byte sequence in the sections scoped memory.
    #  @param self the instance of the object that is invoking this method.
    #  @param sequence the byte sequence we are looking for.
    #  @returns an enumerator of virtual memory addresses where the sequence can be found.
    def locate_byte_sequence_in_scoped_memory(self, sequence:bytearray) -> Iterator[int]:

        memory = self.scoped_memory()
        index = memory.find(sequence, 0)

        while(index > 0):
            yield self.start_address + index
            index = memory.find(sequence, index+1)

        return
        yield


    ## Returns an enumerator of offsets into this region of scoped memory that look like places to inject the current integrity hash.
    #  @param self the instance of the object that is invoking this method.
    #  @returns an enumerator of virtual memory addresses which contain the integrity hash placeholder.
    def integrity_hash_offsets(self) -> Iterator[int]:
        yield from self.locate_byte_sequence_in_scoped_memory(self.INTEGRITY_HASH)
        return
        yield


    ## Returns an enumerator of offsets into this region of scoped memory that look like places to inject the current integrity seed.
    #  @param self the instance of the object that is invoking this method.
    #  @returns an enumerator of virtual memory addresses which contain the integrity seed placeholder.
    def integrity_seed_offsets(self) -> Iterator[int]:
        yield from self.locate_byte_sequence_in_scoped_memory(self.INTEGRITY_SEED)
        return
        yield


    ## Returns an enumerator of offsets which should not be part of the integrity checking.
    #  By default this is just going to return the location of INTEGRITY_HASH usage - however some section types might need to override this
    #  and add more (for instance if we want to XOR the current hash against something to get a known value, that XOR value will need to be 
    #  volatile too).
    #  @param self the instance of the object that is invoking this method.
    #  @returns an enumerator of virtual memory addresses which contain 8-byte QWORDS that should not be integrity checked.
    def volatile_offsets(self) -> Iterator[int]:
        yield from self.integrity_hash_offsets()
        return
        yield


    ## Returns an enumerator of offsets which should be part of the integrity checking (but are still rewritten by this action).
    #  Whilst these values will not change the hash of the binary, they are going to be modified by this action - other actions need to know
    #  this if they intend to make use of the binaries contents.
    #  @param self the instance of the object that is invoking this method.
    #  @returns an enumerator of virtual memory addresses which contain 8-byte QWORDS that will be written by this action (but are still part of the hash).
    def unstable_offsets(self) -> Iterator[Tuple[int, int]]:
        for offset in self.volatile_offsets():
            yield offset, self.SIZE_OF_QWORD
        for offset in self.integrity_seed_offsets():
            yield offset, self.SIZE_OF_QWORD
        return
        yield


    ## Configures and validates intial state information needed for patching non-volatile aspects of the binary.
    #  @param cls the type of class that is invoking this method.
    #  @param sections a list of sections that can be used during initialisation.
    #  @returns the state of the initialisation process on success or None if this section doesn't action anything non-volatile.
    @classmethod
    def configure_non_volatile(cls, sections:List) -> Any:
        return None


    ## Patches aspects of the binary described by this section entry that can be safely incorprated into the hashing process.
    #  These changes will change the hash of the binary but we are able to accomdate that instability (e.g. the hash seed... we know and fix it in the hash process).
    #  @param cls the type of class that is invoking this method.
    #  @param state the state that was generated and should be applied to the binary,
    @classmethod
    def patch_non_volatile(cls, state:Any) -> None:
        return state


    ## Configures and validates intial state information needed for patching volatile aspects of the binary.
    #  @param cls the type of class that is invoking this method.
    #  @param sections a list of sections that can be used during initialisation.
    #  @param state the state generated for the non-volatile patch process
    #  @returns the state of the initialisation process on success or None if this section doesn't action anything volatile.
    @classmethod
    def configure_volatile(cls, sections:List, non_volatile_state:Any) -> Any:
        return None
    
    ## Patches aspects of the binary described by this section entry that are dependant on the hashing process.
    #  These changes will not change the hash of the binary but do depend on its output (typically using or checking the hash). Note that the scope of 
    #  a volatile QWORD is usually a value, not an operation (i.e. in CMP RAX, 0x1122334455667788 you can change what you are looking for - the imm32 but not the operation).
    #  @param cls the type of class that is invoking this method.
    #  @param state the state that was generated and should be applied to the binary,
    @classmethod
    def patch_volatile(cls, state:Any) -> None:
        return


    ## Calculates the expected output of the MurmurOAAT64 hash.
    #  @param self the instance of the object that is invokign this method.
    #  @param seed the seed to provide to the hash algorithm.
    #  @param volatile_qwords a list of offsets to QWORD regions that should be jumped over/skipped when calculating the hash.
    #  @returns the current expected hash of the binary.
    def calculate_murmuroaat64(self, seed:int, volatile_qwords:int) -> int:
        
        murmur = MurmurOaat64(seed)
        
        section = self.elf.get_section_containing(self.start_address)
        current_offset = section.header.sh_addr
        section_ends = current_offset + section.header.sh_size

        for volatile_qword in volatile_qwords:
            static_bytes = self.elf.read(current_offset, volatile_qword - current_offset)
            current_offset = volatile_qword + self.SIZE_OF_QWORD
            murmur.consume(static_bytes)
        
        static_bytes = self.elf.read(current_offset, section_ends - current_offset)
        murmur.consume(static_bytes)

        return int(murmur)