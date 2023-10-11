# python imports
from pathlib import Path

# project imports
from cv.build_steps.base import BuildStep
from cv.common import Environment, E, Paths
from ebp.common.patch_process.patch_manifest import PatchManifest
from ebp.common import HiddenString

## Build step to construct the crackme 32-bit launcher binary
class BuildCrackmeLauncher(BuildStep):


    ## The location of the we should place the built crackme by default.
    DefaultOutputPath = Paths.CvBuildDirectory / "crackme32"


    ## The location of the build script.
    ElfLauncherBuildScript = Paths.ElfBinaryLauncherDirectory / "scripts" / "build-launcher.sh"


    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param build_output the location to place the built binary file.
    def __init__(self, build_output:Path=DefaultOutputPath):
        self.build_output = Path(build_output).resolve()


    ## Builds an environment for the configured arguments.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the environment that was configured.
    def build_environment(self) -> Environment:

        return Environment(
            
            # The location of where to build the binary.
            LAUNCHER_BUILD_DIRECTORY = E.FileDirectory(self.build_output),

            # The name of the file to output.
            LAUNCHER_BUILD_NAME = E.FileName(self.build_output)

        )


    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        environment = self.build_environment()
        process = self.execute([self.ElfLauncherBuildScript], env=environment)
        return self.ExitSuccess(process)