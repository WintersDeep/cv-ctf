# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref MOV_QWORDPTR_RBX_RAX `Self` type
SelfType = TypeVar('SelfType', bound='MOV_DWORDPTR_RBX_EAX')


## Moves the 32bit value in EAX into the memory pointed to by RBX
#  [89 /r](https://www.felixcloutier.com/x86/mov)
class MOV_DWORDPTR_RBX_EAX(x64Instruction):
    

    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 2


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"mov     DWORD PTR[rbx], eax"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [0x89, 0x03]