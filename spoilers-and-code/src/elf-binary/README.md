# 64-bit Crackme ELF Core

This code is for the "internal" 64-bit ELF Crackme code.

It should prompt the user for a password, and if the password is correct, release the final flag of the CV CTF which can be used to open the final ZIP file.

The source for this project is in the [`./spoilers-and-code/src/elf-binary`](./) directory.

## Dependencies

| Dependency Name | Description |
| -- | -- | 
| [`gcc`](https://gcc.gnu.org/) | Build tool used to compile C code.|
| (internal) [`elf-binary-patcher`](../elf-binary-patcher/README.md) / `ebp` | Used to modify and finalise ELF crackme binaries. Whilst not directly used, this tool will be needed after compilation to make the gnerated artifact useful. |

## Compiling

Assuming dependencies are installed compiling this should be as simple as running the `scripts/build-internal.sh` script. Note that the output from this build process is not in a usable state and needs to be patched (see [`cv-builder`](../cv-builder/README.md)  [`elf-binary-patcher`](../elf-binary-patcher/README.md) for more information).

The python tools offer the following relevant/related commands

- `python -m cv build` - to build the whole CV. 
- `python -m cv build-crackme` - to build a _"ready-to-ship"_ ELF binary.
- `python -m cv build-crackme-internal` - which basically runs the above script.
- `python -m cv patch-crackme-internal` - to finish an internal binary and create a stand-alone 64-bit binary.

You can use `ebp` ([`elf-binary-patcher`](../elf-binary-patcher/README.md)) to do specific / partial patching, and data generation.