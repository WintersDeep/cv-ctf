
# python3 imports
from abc import ABC, abstractmethod, abstractproperty, abstractclassmethod
from argparse import ArgumentParser, Namespace
from logging import getLogger
from typing import TypeVar

# third-party imports
from fitz import Rect


## The @ref PatchActionBase `Self` type
PatchActionType = TypeVar('PatchActionType', bound='PatchActionBase')
        

## The base for a patch action class.
#  Patch action classes are used to implement actions that the PDF Patcher can perform.
class PatchActionBase(ABC):

    ## The patcher exited successfully
    ExitSuccess = 0

    ## The patcher exited with failure.
    ExitRuntimeError = 1

    ## Instanciates a new @ref PatchActionBase object.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments that the application is being ran with.
    def __init__(self, arguments:Namespace) -> PatchActionType:
        self.log = getLogger(f"pdfp.action.{self.cli_command}")
        self.arguments = arguments

    ## Creates a rectangle from coordinates.
    #  @param x1 one corners X coordinate.
    #  @param y1 one corners Y coordinate.
    #  @param x2 the other corners X coordinate.
    #  @param y2 the other corners Y coordinate.
    #  @returns a rectangle that represents the given coordinates.
    def create_rectangle(self, x1:int, y1:int, x2:int, y2:int) -> Rect:
        lhs_x = min(x1, x2)
        rhs_x = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        return Rect(lhs_x, top, rhs_x, bottom)


    ## The string entered on the CLI to invoke this action.
    #  This value must be unique else the software will not run (for hopefully obvious reasons).
    @abstractproperty
    def cli_command(self) -> str:
        pass


    ## The help string presented on the CLI for this action when `--help` is used.
    #  This should describe what this action intends to do to the PDF file.
    @abstractproperty
    def cli_help(self) -> str:
        pass


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `PdfPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        pass


    ## Invokes this action.
    #  @returns patch process exit code.
    @abstractmethod
    def __call__(self) -> int:
        # at this point this action will be instanciated, the elf to modify is passed in as an
        # argument and the current program options are available in `self.arguments`
        pass
