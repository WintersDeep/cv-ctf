# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref INC_RBX `Self` type
SelfType = TypeVar('SelfType', bound='INC_RBX')


## Increments the RBX register by a constant value of 1.
#  [REX.W + FF /0](https://www.felixcloutier.com/x86/inc)
class INC_RBX(x64Instruction):


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"inc    rbx"


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 3


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [ 0x48, 0xff, 0xc3 ]