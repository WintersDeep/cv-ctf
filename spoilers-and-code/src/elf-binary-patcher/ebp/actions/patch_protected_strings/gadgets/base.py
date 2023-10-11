# python3 imports
from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from typing import TypeVar, Optional, List, Iterator
from random import randint

# project imports
from ebp.x64asm import (
    x64Instruction, InstructionList,
    INC_RBX, DEC_RBX, 
    ADD_RBX_imm8, SUB_RBX_imm8
)

# third-party imports
from pwnlib.elf import ELF
from elftools.elf.sections import Section



## The @ref StringCharacter `Self` type
StringCharacterType = TypeVar('StringCharacterType', bound='StringCharacter')

## The @ref GadgetBase `Self` type
GadgetBaseType = TypeVar('GadgetBaseType', bound='GadgetBase')

## The @ref PatchState `Self` type
PatchStateType = TypeVar('PatchStateType', bound='PatchState')



## A character in a string.
#  Records a characters value and position within a string.
class StringCharacter(object):

    ## Breaks a binary array down into a ordered list of @ref StringCharacter objects.
    #  @param cls the type of class invoking this method.
    #  @returns a list of string characters that represent the given string.
    @classmethod
    def Manifest(cls, bytearray_:bytearray) -> List[StringCharacterType]:
        return [ cls(i, c) for i, c in enumerate(bytearray_) ]


    ## Instanciates a new @ref StringCharacter object.
    #  @param self the instance of the object that is invoking this method.
    #  @param index the 0-based offset of the character in its parent string.
    #  @param value the ASCII character value that we need to assign at this location.
    def __init__(self, index:int, value:int) -> StringCharacterType:
        self.index = index
        self.value = value


    ## Computes the informal name of this object.
    #  Displays the index, ASCII character and numerical value of this character.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"({self.index},'{chr(self.value)}/0x{self.value:02x}')"


    ## Computes the formal name of this object.
    #  Displays the object information in a manner allowing recomposition of this object.
    #  @returns a technical string that represents the data contained in this object.
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.index}, {self.value})"



## The current state of the patch process.
class PatchState(object):

    ## Instanciates a new @ref PatchState object.
    #  @param self the instance of the object that is invoking this method.
    #  @param elf the ELF file that the data was loaded from.
    #  @param patch_section the section that contains the string we are patching.
    #  @param virtual_memory_address the current virtual memory address where instructions will be inserted.
    #  @param kwargs keyword arguments used as additonal state information.
    def __init__(self, elf:ELF, patch_section:Section, virtual_memory_address:int, **kwargs) -> PatchStateType:
        self.section = patch_section
        self.elf = elf
        self.meta = kwargs



## Base class for gadgets.
#  A base for all gadgets - a gadget is an object that produces assembly that  _"does something"_. 
#  In context all a basic gadget can guarantee is that you can compile it to ASM, and it has a name.
class GadgetBase(ABC):


    ## A friendly name for the gadget for logging.
    @abstractproperty
    def name(self) -> str:
        pass  


    ## Compiles the gadet into assembly instructions.
    #  @param self the instance of the object invoking this method.
    #  @param state the current state of the patch process.
    #  @returns a list of instructions to achieve the gadgets objective.
    @abstractmethod
    def compile(self, state:PatchState) -> InstructionList:
        pass



## A list of gadgets
#  Collectively gadgets work together to achieve a goal. This object just hangs some
#  convienince functions off the native `list`` class.
class GadgetList(list[GadgetBase]):


    ## Returns an iterators expressing each gadget as a list of assembly instructions.
    #  @param self the instance of the object invoking this method.
    #  @param elf the elf binary which we are patching.
    #  @param virtual_memory_address the virtual memory address of the first gadget.
    #  @returns iterator which yields an instruction list for each gadget in the list.
    def compile_blocks_iter(self, elf:ELF, virtual_memory_address:int) -> Iterator[InstructionList]:

        parent_section = elf.get_section_containing(virtual_memory_address)
        patch_state = PatchState(elf, parent_section, virtual_memory_address)

        for gadget in self:
            yield gadget.compile(patch_state)
        return
        yield


    ## Returns a list containing a list of assembly instructions for each gadget.
    #  @param self the instance of the object invoking this method.
    #  @param elf the elf binary which we are patching.
    #  @param virtual_memory_address the virtual memory address of the first gadget.
    #  @returns a list of @ref InstructionList objects.
    def compile_blocks(self, elf:ELF, virtual_memory_address:int) -> list[InstructionList]:
        return [ asm for asm in self.compile_blocks_iter(elf, virtual_memory_address) ]


    ## Returns an iterator of the assembly generated by compiling the gadgets.
    #  @param self the instance of the object invoking this method.
    #  @param elf the elf binary which we are patching.
    #  @param virtual_memory_address the virtual memory address of the first gadget.
    #  @returns iterator which yields instructions for the contained gadgets.
    def compile_flat_iter(self, elf:ELF, virtual_memory_address:int) -> Iterator[x64Instruction]:
        for asm_block in self.compile_blocks_iter(elf, virtual_memory_address):
            yield from asm_block
        return
        yield


    ## Returns a list of the assembly instructions generated by compiling the gadgets.
    #  @param self the instance of the object invoking this method.
    #  @param elf the elf binary which we are patching.
    #  @param virtual_memory_address the virtual memory address of the first gadget.
    #  @returns list of instructions representing the contained gadgets.
    def compile_flat(self, elf:ELF, virtual_memory_address:int) -> InstructionList:
        return InstructionList(self.compile_flat_iter(elf, virtual_memory_address))



## Base class for junk gadgets.
#  Junk gadgets are designed to do pretty much nothing except get in the way and take up space.
class JunkGadget(GadgetBase):
    

    ## Returns the number of bytes this junk gadget occupies.
    @property
    def size(self) -> int:
        pass

    ## Inserts the given gadet randomly into the provided gadget list.
    #  @param cls the type of class executing this method.
    #  @param gadget_instance the instance of the gadget to insert into the @p gadget_list.
    #  @param gadget_list the list into which the gadget should be inserted.
    @classmethod
    def insert_randomly(cls, gadget_instance:GadgetBase, gadget_list:GadgetList) -> None:
        max_index = len(gadget_list)
        chosen_index = randint(0, max_index)
        gadget_list.insert(chosen_index, gadget_instance)


    ## Applies the junk gadget to the given gadget list.
    #  The `apply` method uses @p space_available to determine if it can fit into any remaining space
    #  and if so should create an instance and attach itself to the provided @p gadget_list as is 
    #  appropriate. The return value should be the number of bytes the gadget has consumed (zero if
    #  the gadget decides it is not going to inject itself for any reason).
    #  @param cls the type of class executing this method.
    #  @param space_available the number of bytes available for junk gadgets.
    #  @param gadget_list the current gadget list - this will by modified if a gadget is applied.
    #  @returns the number of bytes this gadget consumed of the remaining space (or 0 if no changes were made).
    @abstractclassmethod
    def apply(cls, space_available:int, gadget_list:GadgetList) -> GadgetBaseType:
        pass



## Base class for assignment gadgets.
#  An assignment gadget is responsible for building one or more characters in from a 
#  protected string in memory. The mechanics of how it goes about this are its own choosing.
class AssignmentGadgetBase(GadgetBase):


    ## Forward knowledge
    #  its useful to be aware of the following:-
    #  - When `compile` is called on an assignmnet gadget the RBX register will always contain
    #    a pointer to a memory location within the protected string currently being built. The exact
    #    location can be determined by looking at the passed `PatchState` objects `meta['rbx_character_index']`
    #    property which indicates the index of the character currently being pointed to.
    #  - The gadget must update this property if its moves RBX. This is usually done using `initialise_state_target`.
    #    this method starts a new InstructionList with instructions required to point RBX at the requested index, and
    #    updates the value accordingly.
    #  - All other general purpose registers are clobberable.
    #  - An assignment gadget must (currently) be a reproducable size - this doesn't mean a fixed size - e.g. two 
    #    instances of the same assignment gadget type can return different number of opcodes when `compile` is called; 
    #    however if the gadgets are compiled again (assuming same state) they must both return the same number of 
    #    opcodes; even if those opcodes are differnt.


    ## Provides assembly instructions to adjust RBX to point at a new string offset
    #  This action is so common, we expect almost every assignment gadget to need to do this at some point.
    #  @tbd this could be made more elaborate / less predictable if really wanted.
    #  @param self the instance of the object that is invoking this method.
    #  @param from_index the index that RBX currently points to.
    #  @param to_index the index we want RBX to point at.
    #  @returns a list of assembly instruction to update RBX to point at the desired location.
    def shift_target(self, from_index:int, to_index:int) -> InstructionList:

        distance = abs(to_index - from_index)
        adjustment_instructions = InstructionList()
        
        # @tbd we could be more fancy and random in building these instructions (use MUL), or build the
        #   adjustment rather than just assign a ADD; for example where we currently do:
        #   ADD RBX, 0x6
        # we could:
        #   XOR RAX, RAX
        #   MOV AL, 0x2
        #   MOV CL, 0x3
        #   MUL CL
        #   ADD RBX, RAX
        
        if to_index > from_index:
            adjustment_instructions.append(
                INC_RBX() if distance == 1 else ADD_RBX_imm8(distance)
            )
        elif to_index < from_index:
            adjustment_instructions.append(
                DEC_RBX() if distance == 1 else SUB_RBX_imm8(distance)
            )
        # else:
        #  the RBX instruction already points where we want it to
        #  no action required.

        return adjustment_instructions


    ## Adjusts the state provided to point at a new index and returns the instructions to achieve this result.
    #  An extention of `shift_target`. Often used to start a new gadget.
    #  @param self the instance of the object that is invoking this method.
    #  @param state the current state of the patch process.
    #  @param to_index the index we want RBX to point at.
    #  @returns a list of assembly instruction to achive the requested outcome.
    def initialise_state_target(self, state:PatchState, new_location:int) -> InstructionList:
        current_location = state.meta.get('rbx_character_index', 0)
        instructions = self.shift_target(current_location, new_location)
        state.meta['rbx_character_index'] = new_location
        return instructions


    ## Given an ordered list of "unclaimed" characters returns a list of indicies from which a N-byte string of consequitive characters can be extracts (where N is @p length).
    #  For example; the XOR64 assignment gadget wants to assign 8-characters at once - this function is used to locate 8 consequitive unclaimed characters.
    #  @param cls the type of class executing this method.
    #  @param unclaimed_characters a list of characters that have not yet been claimed.
    #  @param length the number of consecutive characters we want to select.
    #  @returns List of indicies from which a string of @p length (N) consecutive characters can be taken.
    @classmethod
    def locate_consequitive_characters_of_length(cls, unclaimed_characters:List[StringCharacter], length:int) -> List[int]:
        
        manifest_iterator = enumerate(unclaimed_characters)
        _, last_character = next(manifest_iterator)
        consecutive_groups = []
        consecutive_counter = 1

        for index, character in manifest_iterator:
            if character.index == last_character.index + 1:
                if consecutive_counter >= length - 1:
                    consecutive_groups.append(index - (length -1))
            else:
                consecutive_counter = 0
            
            last_character = character
            consecutive_counter += 1

        return consecutive_groups


    ## Offer this gadget the list of characters that still need to be "built" or are "unclaimed".
    #  This method can chose to return a gadget that will build one or more of the missing characters, or return None if 
    #  is is unable (or unwilling) to do so. If the factory returns a gadget it must remove any "claimed" characters from
    #  the provided list to prevent duplicate assignment. 
    #  @param cls the type of class executing this method.
    #  @param unclaimed_characters a list of character still requiring action.
    #  @returns a gadget instance if characters were "claimed" else None.
    @abstractclassmethod
    def offer(cls, unclaimed_characters:List[StringCharacter]) -> Optional[GadgetBaseType]:
        pass