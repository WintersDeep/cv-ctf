# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref DEC_RBX `Self` type
SelfType = TypeVar('SelfType', bound='DEC_RBX')


## Decrements the RBX register by a constant value of 1.
#  [REX.W + FF /1](https://www.felixcloutier.com/x86/sub)
class DEC_RBX(x64Instruction):


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"dec    rbx"

    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 3


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [ 0x48, 0xff, 0xcb ]