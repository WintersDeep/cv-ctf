# python imports
from pathlib import Path

## The drirectory this script is in.
ThisDirectory = Path(__file__).parent


## A directory of common paths that are of use when building the software.
class Paths(object):

    ## Path of the `cv-builder` application source code.
    CvBuilderProjectDirectory = ThisDirectory.parent.parent

    ## Path of the `cv-builder` applications default build target.
    CvBuildDirectory = CvBuilderProjectDirectory / "build"

    ## Path of the entire projects root `src` directory.
    SrcRootDirectory = CvBuilderProjectDirectory.parent
    
    ## Path of the `assets` directory.
    AssetsDirectory = SrcRootDirectory / "assets"

    ## Path of the `elf-binary-launcher` application source code.
    ElfBinaryLauncherDirectory = SrcRootDirectory / "elf-binary-launcher"

    ## Path of the `elf-binary-patcher` application source code.
    ElfBinaryPatcherDirectory = SrcRootDirectory / "elf-binary-patcher"

    ## Path of the `elf-binary` application source code.
    ElfBinaryDirectory = SrcRootDirectory / "elf-binary"

    ## The `spoilers-and-code` directory.
    SpoilersAndSourceDirectory = SrcRootDirectory.parent

    ## Project root directory.
    ProjectRoot = SpoilersAndSourceDirectory.parent