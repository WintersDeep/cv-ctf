# python3 imports
from abc import ABC, abstractclassmethod, abstractmethod
from typing import TypeVar


## The @ref x64Instruction `Self` type
x64InstructionType = TypeVar('x64InstructionType', bound='x64Instruction')

## The @ref CompilationState `Self` type.
CompilationStateType = TypeVar('CompilationStateType', bound='CompilationState')


## Compilation state of the assembly list.
class CompilationState(object):


    ## Creates a new instance of this object.
    #  @param self the instance of the object that is invoking this method.
    #  @param virtual_memory_address the virtual memory adderss that compilation is currently placing instructions at.
    def __init__(self, virtual_memory_address:int) -> CompilationStateType:
        self.virtual_memory_address = virtual_memory_address

    ## Converts a virtual memory address into an offset relatiev to the current RIP value.
    #  @param self the instance of the object that is invoking this method.
    #  @param asm the assembly instruction currently being injected (needed because by the time it looks at RIP it'll point to the next instruction).
    #  @param virtual_memory_address the address that we are trying to reference.
    #  @returns the relative offset to the requested memory location.
    def vma_to_ripoff(self, asm:x64InstructionType, virtual_memory_address:int) -> int:
        current_rip = self.virtual_memory_address + asm.opcodes_length()
        return virtual_memory_address - current_rip


## A class that represents an x86-64 instruction
class x64Instruction(ABC):

    ## Computes the informal name of this object.
    #  Displays the instruction as INTEL flavor assembly.
    #  @returns a Friendly string that represents the data contained in this object.
    @abstractmethod
    def __str__(self) -> str:
        pass

    ## Compiles this assembly instruction into shellcode.
    #  @param information about the state of the environment where this instruction is being compiled.
    #  @returns bytearray containing this instructions shell code.
    @abstractmethod
    def __call__(self, state:CompilationState) -> bytearray:
        pass
    
    ## Determines the length of this instruction.
    #  @returns the number of bytes used to create this instruction.
    @abstractclassmethod
    def opcodes_length(cls) -> int:
        pass


    ## Converts the virtual memory address to a RIP relative offset.
    #  @param cls the type of class that is invoking this method.
    #  @param current_rip the current location of the RIP register.
    #  @param virtual_memory_address the VMA to translate to a RIP relative offset.
    @classmethod
    def vma_to_ripoff(cls, current_rip, virtual_memory_address):
        current_rip = current_rip + cls.opcodes_length()
        return virtual_memory_address - current_rip