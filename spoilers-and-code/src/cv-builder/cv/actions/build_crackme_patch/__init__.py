
# python3 imports
from argparse import ArgumentParser
from pathlib import Path

# project imports
from cv.actions.base import CvActionBase
from cv.build_steps import BuildCrackmePatchString, BuildCrackmePatchIntegrity


## Patches an internal crackme binary for use.
class BuildCrackmePatchAction(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "patch-crackme-internal"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "patches the crackme internal (64-bit) binary file."

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('-i' ,'--in_file', type=Path,
            default=BuildCrackmePatchString.DefaultPath, help="The location that the unpatched binary can be found." )
        argument_parser.add_argument('-o' ,'--out_file', type=Path,
            default=BuildCrackmePatchString.DefaultPath, help="The location that the patched binary should be placed." )

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitSuccess

        self.log.info(f"Patching the internal crackme binary '{self.arguments.in_file}' for use.")
        
        try:

            self.run_build_steps([
                ("build protected strings", BuildCrackmePatchString(self.arguments.in_file, self.arguments.out_file)),
                ("patch integrity system", BuildCrackmePatchIntegrity(self.arguments.out_file, self.arguments.out_file)),
            ])

            self.log.info(f"Finished patching internal crackme binary at '{self.arguments.out_file}'.")       

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = CvActionBase.ExitRuntimeError
        
        return exit_code
