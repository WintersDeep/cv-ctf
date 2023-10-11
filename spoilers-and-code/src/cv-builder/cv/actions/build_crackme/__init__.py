
# python3 imports
from argparse import ArgumentParser
from pathlib import Path
from tempfile import NamedTemporaryFile

# project imports
from cv.common.paths import Paths
from cv.actions.base import CvActionBase
from cv import build_steps


## Builds the crackme binary from the ground up.
#  This command builds the entire binary from source.
class BuildCrackmeAction(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "build-crackme"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "build the crackme binary."

    ## The default output path if omitted.
    DefaultOutFile = Paths.CvBuildDirectory / "crackme32"

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('-o' ,'--out-file', type=Path,
            default=cls.DefaultOutFile, help="The location that the built internal binary should placed." )
        argument_parser.add_argument('-p', '--password', type=str, required=True,
            help="The password that should unlock the flag for the ELF binary" )
        argument_parser.add_argument('-f', '--flag', type=str, required=True,
            help="The flag that is released with the correct password." )

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitSuccess

        with NamedTemporaryFile() as elf_fh:
            
            elf_build_path = elf_fh.name
            elf_fh.close()

            self.log.info(f"Building the crackme binary at '{elf_build_path}'.")
            
            try:
                
                self.run_build_steps([
                    ("building internal 64-bit binary", build_steps.BuildCrackmeInternal(self.arguments.password, self.arguments.flag, elf_build_path)),
                    ("patching internal binary strings", build_steps.BuildCrackmePatchString(elf_build_path, elf_build_path)),
                    ("patching internal binary integrity", build_steps.BuildCrackmePatchIntegrity(elf_build_path, elf_build_path)),
                    ("generating 32-bit launcher payload data", build_steps.GenerateLaunchpayloadHeader(elf_build_path)),
                    ("building 32-bit launcher", build_steps.BuildCrackmeLauncher(self.arguments.out_file)),
                    ("stripping 32-bit launcher", build_steps.BuildCrackmeStripInternal(self.arguments.out_file, self.arguments.out_file))
                ])

                self.log.info(f"Finished building crackme; final release written to '{self.arguments.out_file}'.")       

            except RuntimeError as ex:
                self.log.error(ex)
                exit_code = CvActionBase.ExitRuntimeError
        
        return exit_code
