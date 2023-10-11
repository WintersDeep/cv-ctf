# python3 imports
from dis import Instruction
from typing import TypeVar, List, Optional, Tuple
from random import choice, randint
from itertools import groupby
from logging import getLogger

# third-party imports
from elftools.elf.sections import Section

# project imports
from .base import AssignmentGadgetBase, PatchState, StringCharacter
from ebp.x64asm import (
    InstructionList,
    x64Instruction, 
    JMP_ripoff,
    MOV_CL_imm8,
    SHL_RDX_CL, 
    XOR_DL_BYTEPTR_ripoff,
    XOR_DL_imm8,
    XOR_RAX_RDX,
    JunkByte
)



## The @ref XorAssignmentBase `Self` type
SelfType = TypeVar('SelfType', bound='XorAssignmentBase')



## This gadget will look for consecutive characters and use an XOR to assign them all at once.
#  The values used to XOR will be sourced from memory rather than use fixed values where possible.
class XorAssignmentBase(AssignmentGadgetBase):
    

    ## List of values we generally steer clear of for this type of assignment.
    ProhibitedValues = [
        0x00, # Really not useful for XOR operations - leaves the remainder to define the value - might was well be direct assignment.
        0x90, # :kludge: 0x90 _could_ be an ASM NOP instruction, ASM NOPs are used to reserve space for patching so this value may change later.
              #    ideal world we would track area's we've identified for patching, for now though its just easier to steer clear.
    ]

    ## The size of the assignment in bytes.
    # @remarks this must be set by derived class types appropriatly.
    Size = 0

    ## The ASM instruction used to pull the appropriate amount of bytes into the general purpose A register from the current RIP offset.
    # @remarks this must be set by derived class types appropriatly.
    MovInCls = None

    ## The ASM instruction used to push the appropriate amount of bytes from the general purpose A register into the memory pointed to by B.
    # @remarks this must be set by derived class types appropriatly.
    MovOutCls = None
    

    ## Instanciates a new @ref DirectByteAssignment object.
    #  @param self the instance of the object that is invoking this method.
    #  @param string_character the string character we need to build/assign.
    def __init__(self, string_characters:List[StringCharacter]):

        assert self.__class__.Size != 0,             f"{self.__class__.__name__} not implemented properly; please set Size"
        assert not self.__class__.MovInCls  is None, f"{self.__class__.__name__} not implemented properly; please set MovInCls"
        assert not self.__class__.MovOutCls is None, f"{self.__class__.__name__} not implemented properly; please set MovOutCls"
        assert string_characters[-1].index - string_characters[0].index == self.__class__.Size - 1, \
            f"unexpected number of string characters selected for {self.__class__.__name__} assignment gadget ({string_characters[-1].index - string_characters[0].index}/{self.__class__.Size - 1})."

        self.log = getLogger(f"ebp.action.patch-protected-strings.xor{self.__class__.Size * 8}")
        self.string_characters = string_characters


    ## Determines the name of this gadget.
    #  @param self the instance of the object that is invoking this method.
    #  @returns string that describes this object behaviour.
    @property
    def name(self) -> str:

        def translate(string_character:StringCharacter):
            byte_value = string_character.value
            char_value = chr(string_character.value)
            return char_value if char_value.isprintable() else f"\\x{byte_value:02x}"

        character_string = "".join( map(translate, self.string_characters))
        hex_string = ", ".join(f"0x{s.value:02x}" for s in self.string_characters)
        return f"{self.Size}-byte XOR operation ('{character_string}' [{hex_string}] at index #{self.string_characters[0].index})"

        
    ## Offer this gadget the a list of characters that still need to be "built".
    #  This method can chose to return a gadget that will build one or more of the missing characters, or return None if 
    #  is is unable (or unwilling) to do so. If the factory returns a gadget it must remove any "claimed" characters from
    #  the provided list to prevent duplicate assignment. 
    #  @param cls the type of class executing this method.
    #  @param unclaimed_characters a list of character still requiring action.
    #  @returns a gadget instance if characters were "claimed" else None.
    @classmethod
    def offer(cls, characters_remaining:List[StringCharacter]) -> Optional[SelfType]:

        generated_gadget = None

        possible_indices = cls.locate_consequitive_characters_of_length(characters_remaining, cls.Size)

        if possible_indices:
            index = choice(possible_indices)
            claimed_characters = characters_remaining[index:index + cls.Size]
            del characters_remaining[index:index + cls.Size]
            return cls(claimed_characters)
            
        return generated_gadget


    ## Discovers a useful series of bytes in the given section that we can use for a XOR base value.
    #  In context this means a series of bytes that do not contain "prohibited values", see the @ref ProhibitedValues
    #  array for which bytes are considered prohibited and why. We only use the current section as this is may be  
    #  position independent executable so we'll be using offsets to grab these values and can only depend on this being
    #  consistent within the current section.
    #  @param section the section to discover the byte sequence in.
    #  @param size the number of consecutive bytes that we want to discover.
    #  @returns a list of indicies that contain consequitive byte regions we can use.
    def discover_xor_byte_sources(self, section:Section, size:int) -> List[int]:

        byte_sources = []    
        current_offset = 0
        byte_validity = lambda byte_: byte_ not in self.ProhibitedValues

        for does_not_contain_prohibited_values, bytes_iter in groupby(section.data(), key=byte_validity):
            
            byte_list = list(bytes_iter)
            bytes_length = len(byte_list)

            if does_not_contain_prohibited_values and bytes_length >= size:
                byte_sources.extend( map(
                    lambda local_offset: current_offset + local_offset,
                    range(bytes_length - (size -1)) 
                ))

            current_offset += len(byte_list)

        self.log.debug(f"Discovered {len(byte_sources)} candidates for {size}-byte sequence used as XOR base value in section at 0x{section.header.sh_addr:08x} - 0x{section.header.sh_addr + section.header.sh_size:08x} ({section.header.sh_size} bytes)")
        
        return byte_sources


    ## Determines a suitable byte sequence for the XOR operation, returning its value and address.
    #  @param section the section to discover the byte sequence in.
    #  @param size the number of consecutive bytes that we want to discover.
    #  @returns tuple containing the VMA the address was found and their actual values. 
    def pick_memory_xor_sequence(self, section:Section, size:int) -> Tuple[ int, List[int] ]:

        max_number_of_attempts = 15

        from ebp.actions import get_volatile_regions
        volatile_regions = get_volatile_regions(section.elffile)

        valid_byte_source_offsets = self.discover_xor_byte_sources(section, size)

        for attempt_index in range(max_number_of_attempts):
        
            self.log.debug(f"Selecting sequence for XOR assignment gadget base from those discovered (attempt #{attempt_index + 1}/{max_number_of_attempts}).")
   
            offset_index = randint(0, len(valid_byte_source_offsets) - 1)
            selected_offset = valid_byte_source_offsets.pop(offset_index)
            virtual_address = section.header.sh_addr + selected_offset
            selected_bytes = section.data()[selected_offset: selected_offset + size]
            
            self.log.debug(f"Selected byte sequence 0x{selected_bytes.hex()} located at 0x{virtual_address:08x} (base+0x{selected_offset}) for XOR base.")

            if volatile_regions.contains(virtual_address, size):
                self.log.debug(f"Attempt failure; one or more bytes falls into a potentially volatile range.")
                continue

            required_xors = [ self.string_characters[i - size].value ^ selected_bytes[i] for i in range(size) ]
            
            if any(byte_ in self.ProhibitedValues for byte_ in required_xors):  
                self.log.debug(f"Attempt failure; requires one or more forbidden characters to produce desired outcome.")
                continue

            self.log.debug(f"Solution accepted; building gadget with chosen byte sequence.")
            return virtual_address, required_xors

        raise RuntimeError(f"Attempted to find an XOR solution without forbidden bytes {max_number_of_attempts} times, but failed.")


    ## Finds the given byte in the current sections memory space.
    #  This is used to source XOR counterparts without requiring to hard code them.
    #  @param section the section to discover a byte in.
    #  @param byte_ the byte to discover
    #  @returns all the positions that byte value appears in the specified section.
    def find_byte_in_section_memory(self, section:Section, byte_:int) -> List[int]:
        
        from ebp.actions import get_volatile_regions
        volatile_regions = get_volatile_regions(section.elffile)
        
        offsets = []
        section_data = section.data()
        index = section_data.find(byte_)

        while index >= 0:
            virtual_memory_address = section.header.sh_addr + index
            if not volatile_regions.contains(virtual_memory_address):
                offsets.append(virtual_memory_address)
            index = section_data.find(byte_, index + 1)

        return offsets


    ## Compiles the gadet into assembly instructions.
    #  @param self the instance of the object invoking this method.
    #  @param state the state of the patch process.
    #  @returns a list of instructions to achieve the outcome.
    def compile(self, state:PatchState) -> InstructionList:

        xor_base_virtual_address, required_xors = self.pick_memory_xor_sequence(state.section, self.__class__.Size)
        state.elf.record_data_dependency(xor_base_virtual_address, len(required_xors), f"XOR base used to obfuscate string for {state.section.name}")
        
        instructions = self.initialise_state_target(state, self.string_characters[0].index)
        
        instructions.append( self.__class__.MovInCls(xor_base_virtual_address) )
        instructions.append( MOV_CL_imm8(8) ) # bits shifted left by SHL (always 8 for one-byte)
        
        for xor_target in reversed(required_xors): # endian inversion.

            byte_addresses_in_memory = self.find_byte_in_section_memory(state.section, xor_target)
            instructions.append( SHL_RDX_CL() )

            if byte_addresses_in_memory:
                char_virtual_address = choice(byte_addresses_in_memory)
                state.elf.record_data_dependency(char_virtual_address, 1, f"XOR key used to obfuscate string for {state.section.name}")
                instructions.append( XOR_DL_BYTEPTR_ripoff(char_virtual_address) )
            elif state.elf.junk_available():
                char_virtual_address = state.elf.assign_junk(xor_target, f"XOR key (taken from junk) used to obfuscate string for {state.section.name}")
                instructions.append( XOR_DL_BYTEPTR_ripoff(char_virtual_address) )
            else:
                instructions.append( XOR_DL_imm8(xor_target) )
                instructions.append( JMP_ripoff(0x01, is_relative=True) ) # these instruction pad out 3-bytes to ensure
                instructions.append( JunkByte( randint(0x00, 0xff) ))     # both assignment types are a 6-byte ASM sequence.

        instructions.append(XOR_RAX_RDX())
        instructions.append(self.__class__.MovOutCls())

        return instructions
