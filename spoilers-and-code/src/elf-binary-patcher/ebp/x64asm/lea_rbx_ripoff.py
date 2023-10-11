# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref LEA_RBX_ripoff `Self` type
SelfType = TypeVar('SelfType', bound='LEA_RBX_ripoff')


## Moves the given address into RBX using a relative RIP offset.
#  [REX.W + 8D /r](https://www.felixcloutier.com/x86/lea)
class LEA_RBX_ripoff(x64Instruction):


    ## Instanciates a new @ref LEA_RBX_ripoff object.
    #  @param self the instance of the object that is invoking this method.
    #  @param address the address to assign into RBX based on offset from RIP.
    def __init__(self, address:int) -> SelfType:
        self.address = address


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"lea     rbx, [rip+0x00000000]  # 0x{self.address:80x}]"


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 7


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        relative_offset = state.vma_to_ripoff(self, self.address)
        offset_bytes = relative_offset.to_bytes(length=4, byteorder='little', signed=True)
        return [0x48, 0x8d, 0x1d] + list(offset_bytes)