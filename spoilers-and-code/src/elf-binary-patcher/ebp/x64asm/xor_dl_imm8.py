# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref XOR_DL_imm8 `Self` type
SelfType = TypeVar('SelfType', bound='XOR_DL_imm8')


## XOR the value in DL with a constant 8-bit value.
#  [80 /6 ib](https://www.felixcloutier.com/x86/xor)
class XOR_DL_imm8(x64Instruction):


    ## Instanciates a new @ref XOR_DL_imm8 object.
    #  @param self the instance of the object that is invoking this method.
    #  @param value the value to use in this expression.
    def __init__(self, value) -> SelfType:
        self.value = value


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 3


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"xor     dl, 0x{self.value:20x}"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [0x80, 0xf2, self.value] 