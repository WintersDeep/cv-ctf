
# python3 imports
from argparse import ArgumentParser
from pathlib import Path

# project imports
from cv.common import Paths, ModifiedContent
from cv.actions.base import CvActionBase
from cv.build_steps import MakeEncryptedZip


## Builds the ZIP containing the crackme-binary.
class BuildFlag3Zip(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "build-flag3-zip"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "creates the ZIP file the crackme binary."

    ## The default file to use as the flag for this ZIP
    DefaultFlagFile = Paths.AssetsDirectory / "flag3-message.txt"

    ## The default file to embed as the crackme binary
    DefaultCrackmeElf = Paths.CvBuildDirectory / "crackme32"

    ## The default file which contains the sign-off/final message.
    DefaultSignOff = Paths.CvBuildDirectory / "final-message.zip"

    ## The default file to use as an output path
    DefaultZipPath = Paths.CvBuildDirectory / "flag3.zip"

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        
        argument_parser.add_argument('-m' ,'--message', type=Path,
            default=BuildFlag3Zip.DefaultFlagFile, help="The location of the default message file." )
        argument_parser.add_argument('-c' ,'--crackme', type=Path,
            default=BuildFlag3Zip.DefaultCrackmeElf, help="The location of the crackme ELF file." )
        argument_parser.add_argument("-f", '--flag', type=str, required=True,
            help="The flag to place in to the flag message document.")
        argument_parser.add_argument('-s' ,'--sign-off', type=Path,
            default=BuildFlag3Zip.DefaultSignOff, help="The location of the ZIP containing the final message." )
        
        argument_parser.add_argument('-p' ,'--password', type=str, required=True, 
            help="The password used for the parting message ZIP file." )
        argument_parser.add_argument('-o' ,'--out_file', type=Path, default=BuildFlag3Zip.DefaultZipPath,
            help="The location to place the ZIP file we create." )

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitSuccess

        self.log.info(f"Creating the flag3 ZIP file at '{self.arguments.out_file}'.")
        
        try:

            with ModifiedContent(self.arguments.message, {
               "INSERT-FLAG3-HERE": self.arguments.flag 
            }) as modified_message:
                
                self.run_build_steps([
                    ("creating zip", MakeEncryptedZip(self.arguments.out_file, self.arguments.password,  { 
                        "README": modified_message,
                        "crackme": self.arguments.crackme,
                        "final-message.zip": self.arguments.sign_off
                    })),
                ])

            self.log.info(f"Finished creating the flag3 ZIP file at '{self.arguments.out_file}'.")

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = CvActionBase.ExitRuntimeError
        
        return exit_code
