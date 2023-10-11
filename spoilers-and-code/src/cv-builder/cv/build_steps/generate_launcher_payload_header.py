# python imports
from pathlib import Path

# project imports
from cv.build_steps.base import BuildStep
from cv.common import Paths

## Generate a `payload.h` for the elf-binary-launcher
class GenerateLaunchpayloadHeader(BuildStep):


    ## The binary path to load as a payload
    DefaultBinaryPath = Paths.CvBuildDirectory / "crackme-internal64"

    ## The default header file to write out to.
    DefaultHeaderPath = Paths.ElfBinaryLauncherDirectory / "src" / "payload.h"


    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param internal64_binary the location of the patched, internal 64-bit binary.
    #  @param header_output the location to write the header data to.
    def __init__(self, internal64_binary:Path=DefaultBinaryPath, header_output:Path=DefaultHeaderPath):
        self.input_path = Path(internal64_binary).resolve()
        self.output_path = Path(header_output).resolve()


    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        process = self.elf_patcher(["write-payload-header", "-o", self.output_path, self.input_path])
        return self.ExitSuccess(process)