#!/bin/bash

# Crude kludge...
# As this patches the binary in random ways its possible that only specific combinations of 
# choices made by the tool will yield corrupt binaries - it shouldn't happen, but this script
# lets us recompile a binary repeatedly to test we get valid builds that don't crash.
#
set -e
count=${2:-1000}
BUILD_NAME="/tmp/build-test-$(date +%s).o"
for index in $(seq $count); do
    echo "build #${index}/${count}"
    python -m ebp -l error "${1}" protect-strings "${BUILD_NAME}"
    chmod +x "${BUILD_NAME}"
    "${BUILD_NAME}"
done
