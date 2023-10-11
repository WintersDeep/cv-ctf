#!/bin/bash

# stop on error
set -e

# location things we are going to need
SCRIPT_DIRECTORY=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
LAUNCHER_PROJECT_DIRECTORY=$(cd ${SCRIPT_DIRECTORY}/.. && pwd)
LAUNCHER_SOURCE_DIRECTORY="${LAUNCHER_PROJECT_DIRECTORY}/src"

# check if custom build targets were set.
if [[ -z "LAUNCH_BUILD_DIRECTORY" ]]; then
LAUNCHER_BUILD_DIRECTORY="${ELF_PROJECT_DIRECTORY}/build"
fi

if [[ -z "LAUNCHER_BUILD_NAME" ]]; then
LAUNCHER_BUILD_NAME="crackme32"
fi

OUTPUT_PATH="${LAUNCHER_BUILD_DIRECTORY}/${LAUNCHER_BUILD_NAME}"

# make sure the build directory exists.
mkdir -p "${LAUNCHER_BUILD_DIRECTORY}"

# build the binary
gcc                                                                         \
    -static                                                                 \
    -Wl,--build-id=none,-z,noseparate-code,-z,common-page-size=32           \
    -fno-asynchronous-unwind-tables                                         \
    -Wno-builtin-declaration-mismatch                                       \
    -Wno-attributes                                                         \
    -Wall -Wextra -Werror                                                   \
    -Wno-all                                                                \
    -nostartfiles                                                           \
    -nostdlib                                                               \
    -nodefaultlibs                                                          \
    -m32                                                                    \
    -s                                                                      \
                                                                            \
    -o "${LAUNCHER_BUILD_DIRECTORY}/${LAUNCHER_BUILD_NAME}"                 \
                                                                            \
    "${LAUNCHER_SOURCE_DIRECTORY}/system32.c"                               \
    "${LAUNCHER_SOURCE_DIRECTORY}/main.c"                                   \
    
# flag binary as executable.
chmod +x "${LAUNCHER_BUILD_DIRECTORY}/${LAUNCHER_BUILD_NAME}"