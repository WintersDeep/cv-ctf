
# python3 imports
from abc import ABC, abstractmethod, abstractproperty
from argparse import ArgumentParser, Namespace
from logging import getLogger
from typing import TypeVar, Iterable, Tuple

# project imports
from cv.build_steps.base import BuildStep

## The @ref CvActionBase `Self` type
CvActionBaseType = TypeVar('CvActionBaseType', bound='CvActionBase')


## The base for a patch action class.
#  Patch action classes are used to implement actions that the PDF Patcher can perform.
class CvActionBase(ABC):

    ## The patcher exited successfully
    ExitSuccess = 0

    ## The patcher exited with failure.
    ExitRuntimeError = 1

    ## Type expressing several build steps that should be completed.
    CompositeBuildSteps = Iterable[Tuple[str, BuildStep]]


    ## Instanciates a new @ref PatchActionBase object.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments that the application is being ran with.
    def __init__(self, arguments:Namespace) -> CvActionBaseType:
        self.log = getLogger(f"cv.action.{self.cli_command}")
        self.arguments = arguments


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


    ## Runs a series of build steps successively
    #  @param self the instance of the object invoking this method.
    #  @param build_steps the list of build steps to be performed.
    def run_build_steps(self, build_steps:CompositeBuildSteps) -> None:
        for step_name, step in build_steps:
            self.log.info(f"Starting to {step_name}...")
            if not step():
                raise RuntimeError(f"Failed to {step_name}; exit code - {step.exit_code}.")
            self.log.info(f"Complete: {step_name}...")
        
    
    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        return self.run_build_steps(self.composite_build_steps)
    



    ## Invokes this action.
    #  @returns patch process exit code.
    @abstractmethod
    def __call__(self) -> int:
        # at this point this action will be instanciated, the elf to modify is passed in as an
        # argument and the current program options are available in `self.arguments`
        pass
