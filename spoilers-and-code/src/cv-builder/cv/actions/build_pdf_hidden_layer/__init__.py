
# python3 imports
from argparse import ArgumentParser
from pathlib import Path
from tempfile import NamedTemporaryFile

# project imports
from cv.common import Paths, ModifiedContent
from cv.actions.base import CvActionBase
from cv.build_steps import PdfAddImageWithTrailingData, PdfInsertBlockQrCode


## Builds the "Hidden" or deleted layer for the PDF.
class BuildPdfHiddenLayer(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "build-pdf-hidden-layer"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "Creates the hidden layer as a PDF - this layer is injected into the CV as a previous version."


    ## The default location to write this data out to.
    DefaultOutFile = Paths.CvBuildDirectory / "hidden-layer.pdf"

    ## The default location to write this data out to.
    DefaultInFile = Paths.AssetsDirectory / "hidden-layer-base.pdf"

    ## The default message to place in the hidden layer QR code.
    DefaultQrMessage = Paths.AssetsDirectory / "flag2-message.txt"

    ## The default image to embed data into.
    DefaultImage = Paths.AssetsDirectory / "hidden-layer-image.png"
    
    ## The default data to append to the end of the image.
    DefaultData = Paths.CvBuildDirectory / "flag3.zip"

    ## The default QR code targetting rectangle
    DefaultQrRect = "0,44,233,182,372"

    ## The default image targetting rectangle
    DefaultImageRect = "0,667,233,805,372"

    ## The default stroke color for inserted QR codes.
    DefaultQrCodeStrokeColor = "rgba(255, 102, 0, 0.8)"

    ## The default fill color for inserted QR codes.
    DefaultQrCodeFillColor = "rgba(255, 102, 0, 0.6)"

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('-i' ,'--in-file', type=Path,
            default=BuildPdfHiddenLayer.DefaultInFile, help="The template document to use as a base for the hidden layer." )
        argument_parser.add_argument('-q', '--qr-message', type=Path,
            default=BuildPdfHiddenLayer.DefaultQrMessage, help="The message to stick into the QR code (the flag will be injected into this)")
        argument_parser.add_argument('-qR', '--qr-rectangle', type=str,
            default=BuildPdfHiddenLayer.DefaultQrRect, help="The location to place the QR code in the document - string in format 'page,x1,y1,x2,y2'.")
        argument_parser.add_argument('-qS', '--qr-stroke', type=str,
            default=BuildPdfHiddenLayer.DefaultQrCodeStrokeColor, help="The default color to stroke cells and blocks in the built QR code.")
        argument_parser.add_argument('-qF', '--qr-fill', type=str,
            default=BuildPdfHiddenLayer.DefaultQrCodeFillColor, help="The default color to fill cells and blocks in the built QR code.")
        argument_parser.add_argument('-I', '--image', type=Path,
            default=BuildPdfHiddenLayer.DefaultImage, help="The image to embed the trailing data")
        argument_parser.add_argument('-IR', '--image-rectangle', type=str,
            default=BuildPdfHiddenLayer.DefaultImageRect, help="The location to place the image in the document - string in format 'page,x1,y1,x2,y2'.")
        argument_parser.add_argument('-d', '--data', type=Path,
            default=BuildPdfHiddenLayer.DefaultData, help="The default trailing data to insert after the image")
        argument_parser.add_argument('-o' ,'--out-file', type=Path,
            default=BuildPdfHiddenLayer.DefaultOutFile, help="The location to place the built PDF document." )
        argument_parser.add_argument('-f' ,'--flag', type=str,
            required=True, help="The flag released by accessing this layer." )
    
    ## Converts a insertion string (5 comma seperated integers) into a page and 4-coord rectangle.
    #  @param cls the type of class that is invoking this method.
    #  @param insertion_string the string to parse
    #  @returns tuple of page number and rectangle coords.
    def insertion_string_to_page_and_rectangle(cls, insertion_string:str) -> tuple[ int, tuple[int, int, int, int ]]:

        str_to_int = lambda str_: int(str_, 0)
        components = insertion_string.split(",")

        if len(components) != 5:
            raise RuntimeError("Invalid number of components in rectangle string; string should take format of \"page,x1,y1,x2,y2\".")
         
        components_int = map(str_to_int, components)
        components_str = map(str, components_int)
        return next(components_str), list(components_str)


    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitSuccess

        self.log.info(f"Creating the hidden layer PDF file at '{self.arguments.out_file}'.")
        
        try:

            qr_page, qr_rectangle = self.insertion_string_to_page_and_rectangle(self.arguments.qr_rectangle)
            image_page, image_rectangle = self.insertion_string_to_page_and_rectangle(self.arguments.image_rectangle)

            with ModifiedContent(self.arguments.qr_message, { "INSERT-FLAG2-HERE": self.arguments.flag }) as qr_message_file:
                 qr_message = qr_message_file.read_text()

            with NamedTemporaryFile() as output_intermediate:

                output_intermediate.close()

                self.run_build_steps([
                    ("inserting qr_code", PdfInsertBlockQrCode(
                        self.arguments.in_file, output_intermediate.name, 
                        *qr_rectangle, qr_message, qr_page, 
                        self.arguments.qr_stroke, self.arguments.qr_fill
                    )),
                    ("inserting image+data", PdfAddImageWithTrailingData(
                        output_intermediate.name,  self.arguments.out_file,
                        *image_rectangle, self.arguments.image, self.arguments.data,
                        image_page
                    )),
                ])

            self.log.info(f"Finished creating hidden layer PDF at '{self.arguments.out_file}'.")

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = CvActionBase.ExitRuntimeError
        
        return exit_code
