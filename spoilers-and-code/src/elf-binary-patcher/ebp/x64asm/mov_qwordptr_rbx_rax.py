# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref MOV_QWORDPTR_RBX_RAX `Self` type
SelfType = TypeVar('SelfType', bound='MOV_QWORDPTR_RBX_RAX')


## Moves the 64bit value in RAX into the memory pointed to by RBX
#  [REX.W + 89 /r](https://www.felixcloutier.com/x86/mov)
class MOV_QWORDPTR_RBX_RAX(x64Instruction):
    

    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 3


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"mov     QWORD PTR[rbx], rax"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [0x48, 0x89, 0x03]