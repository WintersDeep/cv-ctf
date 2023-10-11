
# python3 imports
from argparse import ArgumentParser
from pathlib import Path

# project imports
from cv.common import Paths, ModifiedContent
from cv.actions.base import CvActionBase
from cv.build_steps import MakeEncryptedZip


## Builds the final file ZIP file.
class BuildFinalMessageZip(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "build-final-message-zip"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "creates the ZIP file that has the parting message."

    ## The default file to use as a message template.
    DefaultMessageFile = Paths.AssetsDirectory / "final-message.txt"

    ## The default file to use as a message template.
    DefaultZipPath = Paths.CvBuildDirectory / "final-message.zip"

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        
        argument_parser.add_argument('-m' ,'--message', type=Path,
            default=BuildFinalMessageZip.DefaultMessageFile, help="The location of the parting message template." )
        argument_parser.add_argument("-f", '--flag', type=str, required=True,
            help="The secret pass-phrase to embed in the final message.")
        argument_parser.add_argument('-p' ,'--password', type=str,
            required=True, help="The password used for the parting message ZIP file." )
        argument_parser.add_argument('-o' ,'--out_file', type=Path,
            default=BuildFinalMessageZip.DefaultZipPath, help="The location to place the ZIP file we create." )

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitSuccess

        self.log.info(f"Creating the final message ZIP file at '{self.arguments.out_file}'.")
        
        try:

            with ModifiedContent(self.arguments.message, {
               "INSERT-PASSPHRASE-HERE": self.arguments.flag 
            }) as modified_message:

                self.run_build_steps([
                    ("creating zip", MakeEncryptedZip(self.arguments.out_file, self.arguments.password,  { 
                        "message.txt": modified_message 
                    })),
                ])

            self.log.info(f"Finished creating the final message at '{self.arguments.out_file}'.")

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = CvActionBase.ExitRuntimeError
        
        return exit_code
