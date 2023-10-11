
# python3 imports
from argparse import ArgumentParser, FileType
from typing import List, Type, Any
from pathlib import Path
from re import compile as regex_compile

# third-party imports
from fitz import Rect

# project imports
from pdfp.actions.base import PatchActionBase
from pdfp.common import PdfDocument






## Insert Image With Data
#  Inserts an image into the PDF document which contains trailing information / data.
#  Note that in general software will truncate this data when its extracted so a user will have to be very
#  careful with how they extract it (most tools to "extract images" for instance will work, but will not 
#  return the trailing data as it is discarded when its converted from a PDF stream back to its original format).
class InsertImageWithTrailingData(PatchActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "insert-image-with-data"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "inserts a jpeg file with the exact data stream."


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `PdfPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('pdf', metavar="PDF", type=argument_parser.PdfType, help="The PDF to insert image into.")
        argument_parser.add_argument('x1', type=int, help="Location to insert the image (X coordinate of the first corner).")
        argument_parser.add_argument('y1', type=int, help="Location to insert the image (Y coordinate of the first corner).")
        argument_parser.add_argument('x2', type=int, help="Location to insert the image (X coordinate of the second corner).")
        argument_parser.add_argument('y2', type=int, help="Location to insert the image (Y coordinate of the second corner).")
        argument_parser.add_argument('image', type=FileType('rb'), help="The image file to insert.")
        argument_parser.add_argument('data', type=FileType('rb'), help="The data that should trail after the image.")
        argument_parser.add_argument('out_file', metavar="PDF-OUT", type=Path, help="The location to write the new PDF to." )
        argument_parser.add_argument('-p', '--page', type=int, default=0, help="The page to inject the file into." )


    ## The PDF document data was loaded from.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the current PDF document data is being loaded from.
    @property
    def pdf(self) -> PdfDocument:
        return self.arguments.pdf
    
    
    ## Returns the target rectangle for this action.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the rectangle 
    def target_rect(self) -> Rect:
        return self.create_rectangle(
            self.arguments.x1,
            self.arguments.y1,
            self.arguments.x2,
            self.arguments.y2
        )

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = PatchActionBase.ExitSuccess

        self.log.info(f"Starting JPEG insertion in '{self.pdf.path}'.")
        
        try:

            # load operation parameters
            rect = self.target_rect()
            page = self.pdf.load_page(self.arguments.page)
            data_bytes = self.arguments.data.read()
            image_bytes = self.arguments.image.read()
            
            # insert the image
            img_xref = page.insert_image(rect, stream=image_bytes)

            # update the data to include trailing bytes
            translated_bytes = self.pdf.xref_stream(img_xref)
            self.pdf.update_stream(img_xref, translated_bytes + data_bytes)

            # flush to disk
            self.log.info(f"Finished JPEG insertion in '{self.pdf.path}'.")       
            self.pdf.save(self.arguments.out_file)

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = PatchActionBase.ExitRuntimeError
        
        return exit_code
