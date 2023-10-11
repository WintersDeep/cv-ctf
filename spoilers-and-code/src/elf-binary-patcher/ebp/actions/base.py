
# python3 imports
from abc import ABC, abstractmethod, abstractproperty, abstractclassmethod
from argparse import ArgumentParser, Namespace, ArgumentTypeError
from logging import getLogger
from typing import TypeVar
from pathlib import Path

# project imports
from ebp.common.patch_process import Elf


## The @ref VolatileLocation `Self` type
VolatileLocationType = TypeVar('VolatileLocationType', bound='VolatileLocation')


## Represents a part of the binary that is likely to "change its form"
class VolatileLocation(object):

    ## Creates a new instance of the volatile location.
    #  @param self the instance of the object invoking this method.
    #  @param start the start of the volatile memory region.
    #  @param length the length of the volatile memory region.
    def __init__(self, start:int, length:int) -> VolatileLocationType:
        self.start = start
        self.length = length
        self.end = start + length

    ## Determine if the query range falls into the volatile range.
    #  @param self the instance of the object that is invoking this method.
    #  @param length the size of the query range (used so we can default it easily).
    #  @returns True if there is any overlap between regions else False.
    def contains(self, start:int, length:int=1) -> bool:
        ends = start+length
        return  (start >= self.start and start < self.end) or \
                (ends > self.start and ends <= self.end)   or \
                (start < self.start and ends > self.end)

    def data(self, elf:Elf) -> bytes:
        return elf.read(self.start, self.length)

    def __str__(self) -> str:
        return f"0x{self.start:08x}-0x{self.end:08x} ({self.length} bytes)"


## The @ref VolatileLocationList `Self` type
VolatileLocationListType = TypeVar('VolatileLocationListType', bound='VolatileLocationList')


## Represents a part of the binary that is likely to "change its form"
class VolatileLocationList(list[VolatileLocation]):

    ## Determine if the query range falls into any of the volatile ranges.
    #  @param self the instance of the object that is invoking this method.
    #  @param length the size of the query range (used so we can default it easily).
    #  @returns True if there is any overlap between regions else False.
    def contains(self, start:int, length:int=1) -> bool:
        result = any( vl.contains(start, length) for vl in self )
        return result

    def __str__(self):
        entry_string = lambda index_vl_t: f"- #{index_vl_t[0]} {index_vl_t[1]}"
        return "\n".join(map(entry_string, enumerate(self)))



## The @ref PatchActionBase `Self` type
PatchActionType = TypeVar('PatchActionType', bound='PatchActionBase')
        


## The base for a action class.
#  action classes are used to implement actions that the Elf Binary Patcher can perform.
class ActionBase(ABC):

    ## The patcher exited successfully
    ExitSuccess = 0

    ## The patcher exited with failure.
    ExitRuntimeError = 1

    ## Instanciates a new @ref PatchActionBase object.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments that the application is being ran with.
    def __init__(self, arguments:Namespace) -> PatchActionType:
        self.log = getLogger(f"ebp.action.{self.cli_command}")
        self.arguments = arguments

    ## The string entered on the CLI to invoke this action.
    #  This value must be unique else the software will not run (for hopefully obvious reasons).
    @abstractproperty
    def cli_command(self) -> str:
        pass


    ## The help string presented on the CLI for this action when `--help` is used.
    #  This should describe what this action intends to do to the ELF file.
    @abstractproperty
    def cli_help(self) -> str:
        pass

    ## Invokes this action on an ELF file.
    #  @returns patch process exit code.
    @abstractmethod
    def __call__(self) -> int:
        # at this point this action will be instanciated, the elf to modify is passed in as an
        # argument and the current program options are available in `self.arguments`
        pass



## Base class for patch actions
#  Patch actions which consumes an ELF binary in some manner.
class InPatchActionBase(ActionBase):


    ## Converts an argument into an ELF
    #  @param value the value that was recieved from the command line.
    #  @returns the parsed ELF file.
    @staticmethod
    def ElfType(value:str) -> Elf:
        
        elf_path = Path(value)

        if not elf_path.exists():
            error_message = f'File not found: {elf_path}'
            raise ArgumentTypeError(error_message)

        if not elf_path.is_file():
            error_message = f'Path is not a file: {elf_path}'
            raise ArgumentTypeError(error_message)
    
        return Elf(elf_path, checksec=False)


    ## Gets the ELF binary currently being worked on.
    #  @param self the instance of the object that is being invoked
    #  @returns The ELF binary that this action is scoped to.
    @property
    def elf(self) -> Elf:
        return self.arguments.elf

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `ElfBinaryPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument("elf", metavar="ELF", type=cls.ElfType, 
            help="The ELF file that this tooling should patch.")



## Base class for patch actions
#  Patch actions which mutates an ELF binary in some manner.
class InOutPatchActionBase(InPatchActionBase):

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `ElfBinaryPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        InPatchActionBase.configure_cli_parser(argument_parser)
        argument_parser.add_argument('out_file', metavar="ELF_OUT", type=Path,
            help="The location to write the new ELF with integrity values patched." )
        
    
    ## Returns a list of volatile locations this action is aware of.
    #  This is needed as some actions reflectively pull data from the binary and need to pick locations that
    #  are not going to be subject to change.
    #  @param cls the type of class invoking this method.
    #  @param elf the elf to locate volatile regions in.
    #  @returns a list of volatile regions in the binary.
    @abstractclassmethod
    def volatile_locations(cls, elf:Elf) -> VolatileLocationList:
        pass