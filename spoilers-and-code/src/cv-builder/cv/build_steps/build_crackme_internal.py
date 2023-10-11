# python imports
from pathlib import Path

# project imports
from cv.build_steps.base import BuildStep
from cv.common import Environment, E, Paths
from ebp.common.patch_process.patch_manifest import PatchManifest
from ebp.common import HiddenString

## Build step to construct the crackme 64-bit internal binary
#  Note: this binary is unusable in its output state - it will require patching first.
class BuildCrackmeInternal(BuildStep):


    ## The location of the we should place the built internal crackme by default.
    DefaultOutputPath = Paths.CvBuildDirectory / "crackme-internal64"


    ## The location of the internal crackme build script.
    ElfBinaryBuildScript = Paths.ElfBinaryDirectory / "scripts" / "build-internal.sh"


    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param password the password that the user is expected to enter to unlock the flag.
    #  @param flag the flag that the user should be rewarded with for the correct password.
    #  @param build_output the location to place the partial build binary.
    def __init__(self, password:str, flag:str, build_output:Path=DefaultOutputPath):
        self.build_output = Path(build_output).resolve()
        self.password = password
        self.flag = flag

    ## Gets the patcher manifest path for the binary we are building.
    #  Dubious who should have responsibility for nuking the old manifest - but this is the start action of most build processes so seems a good spot.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the path to the patch manifest file (if one exists) for this binary.
    @property
    def patch_manifest_path(self) -> Path:
        return PatchManifest.elfPathToManifestPath(self.build_output)


    ## Builds an environment for the configured arguments.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the environment that was configured.
    def build_environment(self) -> Environment:

        password = HiddenString(self.password)
        flag = HiddenString(self.flag)

        return Environment(
            
            # C definition passed into GCC via -D argument in build.sh, used with PASSWORD_MASK_STRING
            # to generate the CLI requested password.
            PASSWORD_MT_SEED_QWORD = E.GccUnsignedLong(password.long_seed),

            # C definition passed into GCC via -D argument in build.sh, used with PASSWORD_MT_SEED_QWORD
            # to generate the CLI requested password.
            PASSWORD_MASK_STRING = E.GccString(password.mask_c_string),

            # C definition passed into GCC via -D argument in build.sh, used with PASSWORD_MASK_STRING
            # to generate the CLI requested flag.
            FLAG_MT_SEED_QWORD = E.GccUnsignedLong(flag.long_seed),
            
            # C definition passed into GCC via -D argument in build.sh, used with PASSWORD_MASK_STRING
            # to generate the CLI requested flag.
            FLAG_MASK_STRING = E.GccString(flag.mask_c_string),

            # C definition passed into GCC via -D argument in build.sh, used with PASSWORD_MASK_STRING
            # to generate the CLI requested flag.
            FLAG_RAW_VALUE = E.GccString(flag.raw),

            # The location of where to build the binary.
            ELF_BUILD_DIRECTORY = E.FileDirectory(self.build_output),

            # The name of the file to output.
            ELF_BUILD_NAME = E.FileName(self.build_output)

        )


    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:
        environment = self.build_environment()
        self.patch_manifest_path.unlink(missing_ok=True)
        process = self.execute([self.ElfBinaryBuildScript], env=environment)
        return self.ExitSuccess(process)