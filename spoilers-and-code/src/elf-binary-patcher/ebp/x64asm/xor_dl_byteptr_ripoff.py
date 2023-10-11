# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref XOR_DL_BYTEPTR_ripoff `Self` type
SelfType = TypeVar('SelfType', bound='XOR_DL_BYTEPTR_ripoff')


## XOR the value in DL with the value pointed at by memory at the given offset from RIP.
#  [REX + 32 /r](https://www.felixcloutier.com/x86/xor)
class XOR_DL_BYTEPTR_ripoff(x64Instruction):


    ## Instanciates a new @ref XOR_DL_BYTEPTR_ripoff object.
    #  @param self the instance of the object that is invoking this method.
    #  @param relative_offset the RIP relative offset to read a value from.
    def __init__(self, address) -> SelfType:
        self.address = address


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"xor     dl, BYTE PTR[rip+0x00000000]  # 0x{self.address:08x}]"


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 6


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        relative_offset = state.vma_to_ripoff(self, self.address)
        return [0x32, 0x15] + list(relative_offset.to_bytes(length=4, byteorder='little', signed=True))