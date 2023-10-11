# python imports
from typing import TypeVar

# project imports
from .base import x64Instruction, CompilationState


## The @ref JunkByte `Self` type
SelfType = TypeVar('SelfType', bound='JunkByte')

## A raw / junk byte - this is not generally expected to be executed.
class JunkByte(x64Instruction):

    ## Invoked when a junk byte is compiled
    #  @remarks hooks only receives the address of the junk byte
    JunkByteHook = None

    
    ## Instanciates a new @ref JunkByte object.
    #  @param self the instance of the object that is invoking this method.
    #  @param byte_ the value of the byte to emit here.
    def __init__(self, byte_) -> SelfType:
        self.byte_ = byte_


    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @classmethod
    def opcodes_length(cls) -> int:
        return 1


    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    def __str__(self) -> str:
        return f"JUNK({self.byte_:02x})"


    ## Compiles this assembly instruction into shellcode.
    #  @returns bytearray containing this instructions shell code.
    def __call__(self, state:CompilationState) -> bytearray:
        if(self.JunkByteHook):
            self.JunkByteHook(state.virtual_memory_address)
        return [self.byte_]