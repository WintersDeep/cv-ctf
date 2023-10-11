# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref ADD_RBX_imm8 `Self` type
SelfType = TypeVar('SelfType', bound='JMP_ripoff')

## Increments the RBX register by a constant 8-bit (1 byte) value.
#  [EB cb](https://www.felixcloutier.com/x86/add)
class JMP_ripoff(x64Instruction):


    ## Instanciates a new @ref ADD_RBX_imm8 object.
    #  @param self the instance of the object that is invoking this method.
    #  @param location the location we should jump to.
    #  @param is_relative boolean when True @p location is already relative, else @p location is assumed to be absolute.
    def __init__(self, location, is_relative=False) -> SelfType:
        self.location = location
        self.is_relative = is_relative


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 2


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"jmp    rbx, [rip+0x{self.location:02x}]" if self.is_relative else \
                f"jmp    rbx, {self.location:08x}" 


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        jump_distance = self.location if self.is_relative else \
            state.vma_to_ripoff(self, self.location)
        
        le_bytes_signed = jump_distance.to_bytes(1, 'little', signed=True)
        opcode_unsigned = int.from_bytes(le_bytes_signed, 'little', signed=False)

        return [0xeb, opcode_unsigned]