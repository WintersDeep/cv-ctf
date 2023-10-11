# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref MOV_CL_imm8 `Self` type
SelfType = TypeVar('SelfType', bound='MOV_CL_imm8')


## Moves a constant 8-bit (1 byte) value into the CL register
#  [B0+ rb ib](https://www.felixcloutier.com/x86/mov)
class MOV_CL_imm8(x64Instruction):


    ## Instanciates a new @ref MOV_CL_imm8 object.
    #  @param self the instance of the object that is invoking this method.
    #  @param value the value to assign into the CL register.
    def __init__(self, value) -> SelfType:
        self.value = value


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 2


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"mov     cl,0x{self.value:02x}"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        return [0xb1, self.value]