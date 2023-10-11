
# python3 imports
from argparse import ArgumentParser
from pathlib import Path

# project imports
from cv.actions.base import CvActionBase
from cv.build_steps import GenerateLaunchpayloadHeader, BuildCrackmeLauncher


## Builds the internal crackme binary.
#  Note that the output of this process is an unpatched binary - it will not be useable. 
#  This command is mostly useful during debugging and development as a partial build step. 
class BuildCrackmeLauncherAction(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "build-crackme-launcher"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "build the crackme launcher (32-bit) binary file."


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('-i' ,'--in-file', type=Path,
            default=GenerateLaunchpayloadHeader.DefaultBinaryPath, help="The of the 64-bit binary to embed in the 32-bit launcher." )
        argument_parser.add_argument('-o' ,'--out-file', type=Path,
            default=BuildCrackmeLauncher.DefaultOutputPath, help="The location that the built binary should placed." )


    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitSuccess

        self.log.info(f"Building the crackme binary at '{self.arguments.out_file}'.")
        
        try:
            self.run_build_steps([
                ('generating payload.h', GenerateLaunchpayloadHeader(self.arguments.in_file)),
                ('building launcher', BuildCrackmeLauncher(self.arguments.out_file)),
            ])

            self.log.info(f"Finished building crackme binary at '{self.arguments.out_file}'.")       

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = CvActionBase.ExitRuntimeError
        
        return exit_code
