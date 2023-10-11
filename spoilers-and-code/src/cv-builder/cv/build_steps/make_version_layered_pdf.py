# python imports
from pathlib import Path

# project imports
from cv.build_steps.base import BuildStep
from cv.common import Paths

## Creates a version layered PDF
class MakeVersionLayeredPdf(BuildStep):


    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param pdf_layers the layers of the PDF with the earlier versions being listed first.
    #  @param output_pdf the location to place the modified PDF.
    def __init__(self, pdf_layers:list[Path], output_pdf:Path) -> BuildStep:
        self.pdf_layers = pdf_layers
        self.output_pdf = Path(output_pdf).resolve()
        

    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        return self.ExitSuccess (self.pdf_patcher([
            "version-layered-pdf", self.output_pdf] + self.pdf_layers
        ))

        