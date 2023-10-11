# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref MOV_QWORDPTR_RBX_RAX `Self` type
SelfType = TypeVar('SelfType', bound='MOV_DWORDPTR_RBX_imm8off_imm32')


## Moves the 32bit immediate value into memory pointed to by [RBX + imm8]
#  [C7 /0 id](https://www.felixcloutier.com/x86/mov)
class MOV_DWORDPTR_RBX_imm8off_imm32(x64Instruction):
    
    ## Instanciates a new @ref MOV_DWORDPTR_RBX_imm8off_imm32 object.
    #  @param self the instance of the object that is invoking this method.
    #  @param relative_offset the RIP relative offset to read a value from.
    #  @param signed indicates whether the value is signed or not.
    def __init__(self, offset, value, signed=False) -> SelfType:
        self.offset = offset
        self.value = value
        self.value_signed=signed

    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 7


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"mov     DWORD PTR[rbx + 0x{self.offset:02x}], 0x{self.value:08x}"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        offset_byte = self.offset.to_bytes(length=1, byteorder='little', signed=True)
        value_bytes = self.value.to_bytes(length=4, byteorder='little', signed=self.value_signed)
        return [0xc7, 0x43, self.offset] + list(value_bytes)