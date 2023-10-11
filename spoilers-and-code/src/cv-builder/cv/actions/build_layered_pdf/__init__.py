
# python3 imports
from argparse import ArgumentParser
from pathlib import Path

# project imports
from cv.common import Paths
from cv.actions.base import CvActionBase
from cv.build_steps import MakeVersionLayeredPdf


## Builds a version layered PDF
class BuildLayeredPdf(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "build-layered-pdf"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "Creates a version layered PDF (shim for `ebp` to test integration)."


    ## The default location to write this data out to.
    DefaultOutFile = Paths.CvBuildDirectory / "final-cv.pdf"

    ## The default location to write this data out to.
    DefaultInFiles = [
        Paths.CvBuildDirectory / "hidden-layer.pdf",
        Paths.AssetsDirectory / "cv.pdf"
    ]

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('-p', '--pdf', type=Path, nargs="+",
            default=BuildLayeredPdf.DefaultInFiles, help="The files to layer to build the final PDF." )
        argument_parser.add_argument('-o' ,'--out-file', type=Path,
            default=BuildLayeredPdf.DefaultOutFile, help="The location to place the built PDF document." )
    

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitSuccess

        self.log.info(f"Creating version layered PDF file at '{self.arguments.out_file}'.")
        
        try:

            self.run_build_steps([
                ("layering PDFs", MakeVersionLayeredPdf(
                    self.arguments.pdf, self.arguments.out_file
                )),
            ])

            self.log.info(f"Finished creating version layered PDF at '{self.arguments.out_file}'.")

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = CvActionBase.ExitRuntimeError
        
        return exit_code
