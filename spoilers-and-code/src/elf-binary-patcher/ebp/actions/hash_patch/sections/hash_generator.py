# python imports
from typing import TypeVar, Any, List, Iterator, Tuple
from re import compile as regex_compile
from struct import pack

# third-party imports
from elftools.elf.sections import Section

#project imports
from .base import HashPatchSectionBase
from ebp.x64asm import (InstructionList,
    MOV_DWORDPTR_RBX_imm8off_imm32,
    LEA_RBX_ripoff
)

## The @ref HashGenerator `Self` type
SelfType = TypeVar('SelfType', bound='HashGenerator')


## Represents an integrity hash generator
#  This section defines a region of the .text section which contains a murmur ooat hash generator. It needs 
#  to be patched to skip regions of code that are "volatile" and unsignable, and to be aware of where the 
#  .text section begins. All these changes are non-volatile and part of the binary hash.
class HashGenerator(HashPatchSectionBase):

    ## Magic value that will be replaced in the generator with the start of the .text virtual memory space.
    START_OF_SEGMENT_VIRTUAL_MEMORY = pack(HashPatchSectionBase.QWORD, 0xca11ab1e0ddba115)
    
    ## Magic value that will be replaced with the amount of memory required for the unchecked QWORD list.
    INTEGRITY_CHECK_ALLOC_PLACEHOLD = pack(HashPatchSectionBase.QWORD, 0x5adc01dc0ffeebad)


    ## Creates a new instance of the @ref HashGenerator object.
    #  @param self the instance of the object that is invoking this method.
    #  @param section the section this descriptor was built from.
    #  @param start_address start of region that contains the integrity hash generation.
    #  @param end_address end of the region that contains the integrity hash generation.
    #  @param volatile_qwords the number of volatile QWORDs that space was reserved to patching.
    def __init__(self, section:Section, start_address:int, end_address:int, volatile_qwords:int) -> SelfType:
        super().__init__(section, start_address, end_address)
        self.volatile_qwords = volatile_qwords


    ## Configures and validates intial state information needed for patching.
    #  @param cls the type of class that is invoking this method.
    #  @param sections a list of sections that can be used during initialisation.
    #  @returns the state of the initialisation process on success or None if initialisation did not occur / no processing required.
    @classmethod
    def configure_non_volatile(cls, sections:List) -> Any:

        generator_sections = { }

        volatile_qwords = sections.volatile_offsets()
        number_of_volatile_qwords = len(volatile_qwords)

        if number_of_volatile_qwords > 30:
            # The generator is limited to 30 volatile QWORDS. This is due to the opcodes generated to build the list.
            # It uses instruction c7 43 (MOV RBX+IMM8, IMM32) to assign values into the target buffer. As RBX points 
            # directly to the target buffer we are limited to offsets within a 0->0x7f range. Two potential fixes if
            # we need more offsets:
            #    - would could relocate RBX to point to the target buffer+0x80, then start addressing at offset -0x80
            #      this allows full use of the IMM8 and extends the generator to 62 QWORDS.
            #    - we could walk the address (use 32 or 64 offset, if the above fix is also used), then increment RBX
            #      when we exhaust the IMM8.
            #    - we could change to use instruction c7 83 (MOV RBX+IMM32, IMM32) which gives more offsets than we 
            #      could ever hope to exhaust - however this comes at a size cost (10 bytes instead of 7 for each)
            #      qword in the list.
            # NOTE: this is 30 rather than 32 because we need to reserve two QWORDs:
            #   - one takes us to the end of memory and the other is a stop marker 0xffffffff.
            raise RuntimeError(f"Got {number_of_volatile_qwords} volatile QWORDS, the generator currently does not support more than 32 volatile QWORDS - see source comment for fix")

        for generator in sections:

            if isinstance(generator, cls):

                generator_sections[generator] = volatile_qwords
                
                if generator.volatile_qwords < number_of_volatile_qwords:
                    raise RuntimeError(f"generator identified by section {generator.section.name} reserved space for {generator.volatile_qwords} volatile qwords but it needs space for {number_of_volatile_qwords}. set `#define NUMBER_OF_VOLATILE_QWORDS {number_of_volatile_qwords}`.")
                elif generator.volatile_qwords > number_of_volatile_qwords:
                    cls.Log.warning(f"generator identified by section {generator.section.name} reserved space for {generator.volatile_qwords}  volatile qwords but it only needs space for {number_of_volatile_qwords}. set `#define NUMBER_OF_VOLATILE_QWORDS {number_of_volatile_qwords}`.")
                else:
                    cls.Log.debug(f"generator identified by section {generator.section.name} reserved space for {generator.volatile_qwords}  volatile qwords - this is the expected value.")

        return generator_sections


    ## Finds the .text space reserved to build the unsafe QWORD list and collect the virtual memory start address.
    #  The C code should have created us a perfectly size space to drop assembly into, this will be defined by a large number of NOP's 
    #  injected into the code. This code finds that space so we know where to inject out instructions.
    #  @param self the instance of the object that is invoking this method.
    #  @param volatile_qwords the list of volatile QWORD offsets we need to accomodate.
    #  @returns the location of the space reserved for patching the generator.
    def find_patch_reserved_space(self, volatile_qwords:List[int]) -> int:
        
        size_of_patch__qword_list = (len(volatile_qwords) + 2) * 7  # space needed for instructions to build list of for all QWORDS, a "virtual" marker for end of section, and a STOP marker (0xffffffff)
        size_of_patch__vma_start = 7                                # space needed for single LEA instruction to bring VMA start address into RBX.
        
        required_patch_size = sum([
            size_of_patch__qword_list,
            size_of_patch__vma_start
        ])

        reservation_regex = regex_compile(b"\x90{%i,}" % required_patch_size)
        reservation_matches = list( reservation_regex.finditer( self.scoped_memory() ) )

        if not reservation_matches:
            raise RuntimeError(f"generator identified by section {self.section.name} needs a reservation of {required_patch_size} bytes, but we failed to find one.")
        elif len(reservation_matches) > 1:
            raise RuntimeError(f"generator identified by section {self.section.name} needs a reservation of {required_patch_size} bytes and we found multiple?")

        reservation_start = reservation_matches[0].start()
        reservation_memory = self.start_address + reservation_start
        reservation_length = reservation_matches[0].end() - reservation_start
        self.Log.debug(f"found reservation for {self.section.name} at 0x{reservation_memory:016x} ({reservation_length}/{required_patch_size} bytes)")

        return reservation_memory, reservation_length
        

    ## Creates x86-64 instructions which build the "skips" array.
    #  The hash mechanism "skips" over "volatile" QWORDS - things we need in the binary, but can't know before hashing (such as the binary hash itself).
    #  This is done by a consulting a list of offsets - at each offset the generator will jump 8-bytes. The offsets define where the volatile QWORDS are.
    #  Two final entries are made in the list - one that will cause a read to end of section memory, and another to indicate to the iterator its finished.
    #  This function builds the assembly that generates this list.
    #  @NOTE this code builds assemly that expects RBX to point at a memory address which contains sufficient space to build the skip array.
    #  @param volatile_qwords the list of offsets where volatile QWORDs are located in memory.
    #  @param virtual_memory_start the start address of the sections virtual memory.
    #  @param virtuam_memory_ends the end address of the sections virtual memory.
    #  @returns a list of instructions that will build the required skip array.
    def create_asm__build_skips_array(self, volatile_qwords:List[int], virtual_memory_start:int, virtual_memory_ends:int) -> InstructionList:
        
        index = 0
        instructions = InstructionList()
        current_offset = virtual_memory_start

        for index, qword in enumerate(volatile_qwords):
            instruction = MOV_DWORDPTR_RBX_imm8off_imm32(index * self.SIZE_OF_DWORD, qword - current_offset)
            instructions.append(instruction)
            current_offset = qword + self.SIZE_OF_QWORD

        end_marker = MOV_DWORDPTR_RBX_imm8off_imm32((index + 1) * self.SIZE_OF_DWORD, virtual_memory_ends - current_offset)
        stop_marker = MOV_DWORDPTR_RBX_imm8off_imm32((index + 2) * self.SIZE_OF_DWORD, 0xffffffff)
        instructions.append(end_marker)
        instructions.append(stop_marker)
        
        return instructions

    
    ## Creates x86-64 instructions which return the start of section memory
    #  The generator needs to know where its section starts, it expects this to be placed into RBX when the patch finishes.
    #  @param self the instance of the object that is invoking this method.
    #  @param start_of_memory the address that this sections memory starts at.
    #  @returns instructions which return the start of section memory to the function via RBX.
    def create_asm__return_start_virtual_memory(self, start_of_memory:int) -> InstructionList: 
        instructions = InstructionList()
        instruction = LEA_RBX_ripoff(start_of_memory)
        instructions.append(instruction)
        return instructions


    ## Patches the generators memory allocation to be a size that will accomodate the skip array.
    #  NOTE: the skip array needs to be sized of acommodate N long/qwords; where N is the number of volatile offsets,
    #    +1 skip to reach the end of section memory, +1 entry for the STOP marker (0xffffffff)
    #  @param self the instance of the object that is invoking this method.
    #  @param volatile_qwords the list of volatile qword offsets.
    def patch_non_volatile__memory_allocation_size(self, volatile_qwords:List[int]) -> None:
        target_bytes = self.INTEGRITY_CHECK_ALLOC_PLACEHOLD
        volatile_memory_alloc_size = (len(volatile_qwords) + 2) * self.SIZE_OF_QWORD
        volatile_memory_alloc_bytes = pack(self.QWORD, volatile_memory_alloc_size)
        for index in self.locate_byte_sequence_in_scoped_memory(target_bytes):
            self.elf.write(index, volatile_memory_alloc_bytes)


    ## Patches the generator where additional instructions are required.
    #  This adds instructions to the generator for two things:
    #    - to build the "skip array" of volatile QWORDS offsets.
    #    - to return the start of section memory in RBX.
    #  @param self the instance of the object that is invoking this method.
    #  @param volatile_qwords the list of volatile qword offsets.
    def patch_non_volatile__volatile_qwords_array_and_start_address(self, volatile_qwords:List[int]) -> None:
        
        patch_space, patch_size = self.find_patch_reserved_space(volatile_qwords)

        section = self.elf.get_section_containing(self.start_address)
        section_starts = section.header.sh_addr
        section_ends = section_starts + section.header.sh_size

        build_skip_array_instructions       = self.create_asm__build_skips_array(volatile_qwords, section_starts, section_ends)
        return_start_of_memory_instructions = self.create_asm__return_start_virtual_memory(section_starts)

        patch_instructions = InstructionList()
        patch_instructions.extend( build_skip_array_instructions )
        patch_instructions.extend( return_start_of_memory_instructions )

        opcodes = patch_instructions.opcodes(patch_space)

        assert len(opcodes) <= patch_size, \
            "ASM generated to build QWORD array and assign start address for hash generator exceeded space reserved for this purpose."

        self.elf.write(patch_space, opcodes)
        

    ## Patches aspects of the binary described by this section entry that can be safely incorprated into the hashing process.
    #  These changes will change the hash of the binary but we are able to accomdate that instability (e.g. the hash seed... we know and fix it in the hash process).
    #  @param cls the type of class that is invoking this method.
    #  @param state the state that was generated and should be applied to the binary,
    @classmethod
    def patch_non_volatile(cls, state:Any) -> None:
        
        for generator, volatile_qwords in state.items():
            generator.patch_non_volatile__memory_allocation_size(volatile_qwords)
            generator.patch_non_volatile__volatile_qwords_array_and_start_address(volatile_qwords)

    ## Returns an enumerator of offsets which should be part of the integrity checking (but are still rewritten by this action).
    #  Whilst these values will not change the hash of the binary, they are going to be modified by this action - other actions need to know
    #  this if they intend to make use of the binaries contents.
    #  @param self the instance of the object that is invoking this method.
    #  @returns an enumerator of virtual memory addresses which contain 8-byte QWORDS that will be written by this action (but are still part of the hash).
    def unstable_offsets(self) -> Iterator[Tuple[int, int]]:
        yield from ( (addr, self.SIZE_OF_QWORD) for addr in self.locate_byte_sequence_in_scoped_memory(self.INTEGRITY_CHECK_ALLOC_PLACEHOLD) )
        try:
            yield self.find_patch_reserved_space([])
        except RuntimeError: # generator likely already patched.
            pass
        return