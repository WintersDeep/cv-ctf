# python imports
from pathlib import Path

# project imports
from cv.build_steps.base import BuildStep
from cv.common import Paths

## Removes all the gubbins from the crackme32 binary and messes with the ELF header.
class BuildCrackmeStripInternal(BuildStep):


    ## The binary path to load as a payload
    DefaultBinaryPath = Paths.CvBuildDirectory / "crackme32"

    ## The default header file to write out to.
    DefaultHeaderPath = Paths.CvBuildDirectory / "crackme32-stripped"


    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param crackme32 the location of the 32-bit binary.
    #  @param crackme32_stripped the to write the stripped binary to.
    def __init__(self, crackme32:Path=DefaultBinaryPath, crackme32_stripped:Path=DefaultHeaderPath):
        self.input_path = Path(crackme32).resolve()
        self.output_path = Path(crackme32_stripped).resolve()


    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        process = self.elf_patcher(["strip-binary", self.input_path, self.output_path])
        return self.ExitSuccess(process)