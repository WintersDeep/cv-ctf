# python imports
from pathlib import Path

# project imports
from cv.build_steps.base import BuildStep
from cv.common import Paths

## Adds a QR code to the PDF.
class PdfInsertBlockQrCode(BuildStep):


    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param original_pdf the location from which to load PDF data.
    #  @param output_pdf the location to place the modified PDF.
    #  @param x1 the left-most edge of the location to inject the QR code.
    #  @param y1 the top-most edge of the location to inject the QR code.
    #  @param x2 the right-most edge of the location to inject the QR code.
    #  @param y2 the bottom-most edge of the location to inject the QR code.
    #  @param message the message to put into the QR code.
    #  @param page the page to place the image on to
    #  @param stroke_color the stroke color to draw QR code blocks with.
    #  @param fill_color the fill color to draw QR code blocks with.
    def __init__(self, original_pdf:Path, output_pdf:Path, x1:int, y1:int, x2:int, y2:int, message:str, page:int, stroke_color:str, fill_color:str) -> BuildStep:
        self.original_pdf = Path(original_pdf).resolve()
        self.output_pdf = Path(output_pdf).resolve()
        self.message = message
        self.rectangle = [x1, y1, x2, y2]
        self.page = page
        self.stroke_color = stroke_color
        self.fill_color = fill_color
        

    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        process = self.pdf_patcher([
            "insert-qr-code", self.original_pdf] + self.rectangle + [self.message, self.output_pdf, 
            "-p", self.page, '-f', self.fill_color, '-s', self.stroke_color 
        ])


        return self.ExitSuccess(process)