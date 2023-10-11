#!/bin/bash

# determine file locations
TEMP_PREFIX="/tmp/preview-asm-$(date +%s)"
TEMP_ASM_FILE="${TEMP_PREFIX}.asm"
TEMP_OBJ_FILE="${TEMP_PREFIX}.o"

# dump asm to temp file
echo "${1}" > "${TEMP_ASM_FILE}"

# compile asm to temp file
nasm -felf64 "${TEMP_ASM_FILE}" -o "${TEMP_OBJ_FILE}" 

# if compiled display and remove temp file
if [ -f "${TEMP_OBJ_FILE}" ]; then
    objdump -M intel -d "${TEMP_OBJ_FILE}"
    objdump -M att -d "${TEMP_OBJ_FILE}"
    rm -rf "${TEMP_OBJ_FILE}"
fi

# remove temp asm file too.
rm -rf "${TEMP_ASM_FILE}"