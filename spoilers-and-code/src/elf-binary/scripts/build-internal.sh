#!/bin/bash

# stop on error
set -e

# location things we are going to need
SCRIPT_DIRECTORY=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ELF_PROJECT_DIRECTORY=$(cd ${SCRIPT_DIRECTORY}/.. && pwd)
ELF_SOURCE_DIRECTORY="${ELF_PROJECT_DIRECTORY}/src"

# build any compiler definitions coming in from the environment
COMPILER_DEFINITIONS=()

DEFINITION_ENVIRONMENT_VARIABLES=(                \
  "PASSWORD_MT_SEED_QWORD"                        \
  "PASSWORD_MASK_STRING"                          \
  "FLAG_MT_SEED_QWORD"                            \
  "FLAG_MASK_STRING"                              \
  "FLAG_RAW_VALUE"                                \
)

for DEFINITION_VARIABLE in "${DEFINITION_ENVIRONMENT_VARIABLES[@]}"
do
  if [[ ! -z "${!DEFINITION_VARIABLE}" ]]; then
    COMPILER_DEFINITIONS+=("-D${DEFINITION_VARIABLE}=${!DEFINITION_VARIABLE}")
  fi
done


# check if custom build targets were set.
if [[ -z "ELF_BUILD_DIRECTORY" ]]; then
ELF_BUILD_DIRECTORY="${ELF_PROJECT_DIRECTORY}/build"
fi

if [[ -z "ELF_BUILD_NAME" ]]; then
ELF_BUILD_NAME="crackme-internal"
fi


# make sure the build directory exists.
mkdir -p "${ELF_BUILD_DIRECTORY}"

# build the binary
gcc                                                                         \
    -static                                                                 \
    -Wl,--build-id=none,-z,noseparate-code,-z,common-page-size=32           \
    -fno-asynchronous-unwind-tables                                         \
    -Wno-attributes                                                         \
    -Wall -Wextra -Werror                                                   \
    -Wno-all                                                                \
    -nostartfiles                                                           \
    -nostdlib                                                               \
    -nodefaultlibs                                                          \
    -m64                                                                    \
    -s                                                                      \
                                                                            \
    "${COMPILER_DEFINITIONS[@]}"                                            \
                                                                            \
    -T "${ELF_SOURCE_DIRECTORY}/script.lds"                                 \
    -o "${ELF_BUILD_DIRECTORY}/${ELF_BUILD_NAME}"                           \
                                                                            \
    "${ELF_SOURCE_DIRECTORY}/crackme.c"                                     \
    "${ELF_SOURCE_DIRECTORY}/memory.c"                                      \
    "${ELF_SOURCE_DIRECTORY}/system64.c"                                    \
    "${ELF_SOURCE_DIRECTORY}/common.c"                                      \
    "${ELF_SOURCE_DIRECTORY}/integrity.c"                                   \
    "${ELF_SOURCE_DIRECTORY}/twister.c"                                     \
    

# flag binary as executable.
chmod +x "${ELF_BUILD_DIRECTORY}/${ELF_BUILD_NAME}"