# python3 imports
from typing import TypeVar, List, Optional
from random import randint
from unittest.util import strclass

# project imports
from .base import AssignmentGadgetBase, PatchState, StringCharacter
from ebp.x64asm import InstructionList, MOV_BYTEPTR_RBX_imm8


## The @ref DirectByteAssignment `Self` type
SelfType = TypeVar('SelfType', bound='DirectByteAssignment')


## Simple gadget that simply assigns a specific character its value directly.
class DirectByteAssignment(AssignmentGadgetBase):


    ## Instanciates a new @ref DirectByteAssignment object.
    #  @param self the instance of the object that is invoking this method.
    #  @param string_character the string character we need to build/assign.
    def __init__(self, string_character:StringCharacter):
        self.string_character = string_character


    ## Offer this gadget the a list of characters that still need to be "built".
    #  This method can chose to return a gadget that will build one or more of the missing characters, or return None if 
    #  is is unable (or unwilling) to do so. If the factory returns a gadget it must remove any "claimed" characters from
    #  the provided list to prevent duplicate assignment. 
    #  @param cls the type of class executing this method.
    #  @param unclaimed_characters a list of character still requiring action.
    #  @returns a gadget instance if characters were "claimed" else None.
    @classmethod
    def offer(cls, characters_remaining:List[StringCharacter]) -> Optional[SelfType]:
        # this gadet will always claim a character to assign at random.
        take_index = randint(0, len(characters_remaining) - 1)
        string_char = characters_remaining.pop(take_index)
        return cls(string_char)

    ## Determines the name of this gadget.
    #  @param self the instance of the object that is invoking this method.
    #  @returns string that describes this object behaviour.
    @property
    def name(self) -> str:
        byte_value = self.string_character.value
        char_value = chr(self.string_character.value)
        display_value = f"'{char_value}' (0x{byte_value:02x})" if char_value.isprintable() else f"0x{byte_value:02x}"
        return f"direct byte assignment ({display_value} to index #{self.string_character.index})"


    ## Compiles the gadet into assembly instructions.
    #  @param self the instance of the object invoking this method.
    #  @param state the state of the patch process.
    #  @returns a list of instructions to achieve the outcome.
    def compile(self, state:PatchState) -> InstructionList:
        instructions = self.initialise_state_target(state, self.string_character.index)       
        instructions.append(MOV_BYTEPTR_RBX_imm8(self.string_character.value))
        return instructions