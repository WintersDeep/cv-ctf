# python3 imports
from typing import TypeVar, List
from random import randint

# project imports
from .base import JunkGadget, PatchState, GadgetList
from ebp.x64asm import InstructionList, JMP_ripoff, JunkByte


## The @ref MisalignedJump `Self` type
SelfType = TypeVar('SelfType', bound='MisalignedJump')


## Gadget that performs a jump into mis-aligned instructions.
#  Inserts a JMP then the start of another instruction (usually)- the JMP is targetted just past this junk byte
#  the effect is that code flow jumps over the byte but a decompiler may get confused and just keep rolling.
#  @tbd pick bytes to target specfically multi-byte instructions - wide enough selection to be unpredictable.
#  @tbd expand junk range to be variable size (jump N bytes)
class MisalignedJump(JunkGadget):


    ## The name of this gadget.
    name = "jump/junk gadget."

    ## The size of this gadget.
    size = JMP_ripoff.opcodes_length() + JunkByte.opcodes_length()

    ## Applies the junk gadget to the given gadget list.
    #  @param cls the type of class executing this method.
    #  @param space_available the number of bytes available for junk gadgets.
    #  @param gadget_list the current gadget list - this will by modified if a gadget is applied.
    #  @returns the instance of the gadget that was created and inserted into @p gadget_list (if one was created), else None.
    @classmethod
    def apply(cls, space_available, gadget_list:GadgetList) -> JunkGadget:
        
        gadget_instance = None

        if space_available >= cls.size:
            gadget_instance = cls()
            cls.insert_randomly( gadget_instance, gadget_list)

        return gadget_instance


    ## Compiles the gadet into assembly instructions.
    #  @param self the instance of the object invoking this method.
    #  @param state the state of the patch process.
    #  @returns a list of instructions to achieve the outcome.
    def compile(self, state:PatchState) -> InstructionList:
        instructions =  InstructionList()
        instructions.append(JMP_ripoff(0x01, is_relative=True))
        instructions.append(JunkByte( randint(0x00, 0xff) ))
        return instructions

        
        
