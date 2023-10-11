# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref SHL_RDX_CL `Self` type
SelfType = TypeVar('SelfType', bound='SHL_RDX_CL')


## Shift the RDX register left by the number of bits specified in the CL register.
#  [REX.W + D3 /5](https://www.felixcloutier.com/x86/sal:sar:shl:shr)
class SHL_RDX_CL(x64Instruction):


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 3


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"shl     rdx, cl"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [0x48, 0xd3, 0xe2]