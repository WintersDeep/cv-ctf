# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref MOV_RAX_QWORDPTR_ripoff `Self` type
SelfType = TypeVar('SelfType', bound='MOV_RAX_QWORDPTR_ripoff')


## Moves the 8-byte (64-bit) value in memory at the given offset from the RIP into RAX.
#  [REX.W + 8B /r](https://www.felixcloutier.com/x86/mov)
class MOV_RAX_QWORDPTR_ripoff(x64Instruction):


    ## Instanciates a new @ref MOV_RAX_QWORDPTR_ripoff object.
    #  @param self the instance of the object that is invoking this method.
    #  @param relative_offset the RIP relative offset to read a value from.
    def __init__(self, address:int) -> SelfType:
        self.address = address


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"mov     rax, QWORD PTR[rip+0x00000000]  # 0x{self.address:80x}]"


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 7


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        relative_offset = state.vma_to_ripoff(self, self.address)
        return [0x48, 0x8b, 0x05] + list(relative_offset.to_bytes(length=4, byteorder='little', signed=True))