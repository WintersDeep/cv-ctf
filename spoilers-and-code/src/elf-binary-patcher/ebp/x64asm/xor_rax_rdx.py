# python imports
from typing import TypeVar

# project imports
from .base import CompilationState, x64Instruction


## The @ref XOR_RAX_RDX `Self` type
SelfType = TypeVar('SelfType', bound='XOR_RAX_RDX')


## XOR the value in RAX with the value in RDX.
#  [80 /6 ib](https://www.felixcloutier.com/x86/xor)
class XOR_RAX_RDX(x64Instruction):


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 3


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"xor     rax, rdx"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [0x48, 0x31, 0xd0] 