# python imports
from pathlib import Path

# project imports
from cv.build_steps.base import BuildStep
from cv.common import Paths

## Patches the integrity components of a partial internal crackme binary.
#  Note: this binary is may be unusable in its output state - it may require further patching.
#    although this is usually the last aspect of the patching process...
class BuildCrackmePatchIntegrity(BuildStep):


    ## The location of the we should place the built internal crackme by default.
    DefaultPath = Paths.CvBuildDirectory / "crackme-internal64"


    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param unpatched_input the location of the unpatched binary.
    #  @param build_output the location to write the patched binary to.
    def __init__(self, unpatched_input:Path=DefaultPath, build_output:Path=DefaultPath):
        self.input_path = Path(unpatched_input).resolve()
        self.output_path = Path(build_output).resolve()


    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        process = self.elf_patcher(["hash-patch", self.input_path, self.output_path])
        return self.ExitSuccess(process)