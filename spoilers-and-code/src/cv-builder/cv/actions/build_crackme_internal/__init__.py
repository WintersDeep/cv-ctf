
# python3 imports
from argparse import ArgumentParser
from pathlib import Path

# project imports
from cv.actions.base import CvActionBase
from cv.build_steps import BuildCrackmeInternal


## Builds the internal crackme binary.
#  Note that the output of this process is an unpatched binary - it will not be useable. 
#  This command is mostly useful during debugging and development as a partial build step. 
class BuildCrackmeInternalAction(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "build-crackme-internal"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "build the crackme internal (64-bit) binary file."

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('-o' ,'--out_file', type=Path,
            default=BuildCrackmeInternal.DefaultOutputPath, help="The location that the built internal binary should placed." )
        argument_parser.add_argument('-p', '--password', type=str, required=True,
            help="The password that should unlock the flag for the ELF binary" )
        argument_parser.add_argument('-f', '--flag', type=str, required=True,
            help="The flag that is released with the correct password." )

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitSuccess

        self.log.info(f"Building the internal crackme binary at '{self.arguments.out_file}'.")
        
        try:
            build_step = BuildCrackmeInternal(self.arguments.password, self.arguments.flag, self.arguments.out_file)
            if not build_step(): raise RuntimeError(f"Failed to build internal crackme; exit code - {build_step.exit_code}")
            self.log.info(f"Finished building internal crackme binary at '{self.arguments.out_file}'.")       

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = CvActionBase.ExitRuntimeError
        
        return exit_code
