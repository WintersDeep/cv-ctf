# python imports
from pathlib import Path

# project imports
from cv.build_steps.base import BuildStep
from cv.common import Paths

## Adds an image to a PDF document which includes trailing data.
class PdfAddImageWithTrailingData(BuildStep):


    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param original_pdf the location from which to load PDF data.
    #  @param output_pdf the location to place the modified PDF.
    #  @param x1 the left-most edge of the location to inject the image.
    #  @param y1 the top-most edge of the location to inject the image.
    #  @param x2 the right-most edge of the location to inject the image.
    #  @param y2 the bottom-most edge of the location to inject the image.
    #  @param image the path to the image to be embedded in the original pdf.
    #  @param data the data to append to the injected image.
    #  @param page the page to place the image on to
    def __init__(self, original_pdf:Path, output_pdf:Path, x1:int, y1:int, x2:int, y2:int, image:Path, data:Path, page:int) -> BuildStep:
        self.original_pdf = Path(original_pdf).resolve()
        self.output_pdf = Path(output_pdf).resolve()
        self.image = Path(image).resolve()
        self.data = Path(data).resolve()
        self.rectangle = [x1, y1, x2, y2]
        self.page = page


    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        process = self.pdf_patcher(["insert-image-with-data", self.original_pdf] + self.rectangle + [self.image, self.data, self.output_pdf, "-p", self.page ])

        return self.ExitSuccess(process)