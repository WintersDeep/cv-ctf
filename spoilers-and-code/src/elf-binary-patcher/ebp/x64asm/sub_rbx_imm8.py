# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref SUB_RBX_imm8 `Self` type
SelfType = TypeVar('SelfType', bound='SUB_RBX_imm8')


## Decrements the RBX register by a constant 8-bit (1 byte) value.
#  [RREX.W + 83 /5 ib](https://www.felixcloutier.com/x86/sub)
class SUB_RBX_imm8(x64Instruction):


    ## Instanciates a new @ref SUB_RBX_imm8 object.
    #  @param self the instance of the object that is invoking this method.
    #  @param distance the amount of distance we expect to increment this value by.
    def __init__(self, distance) -> SelfType:
        self.distance = distance


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 4


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"sub    rbx, 0x{self.distance:02x}"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [0x48, 0x83, 0xeb, self.distance]