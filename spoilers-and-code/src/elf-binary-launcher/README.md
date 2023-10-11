# 32-bit Crackme ELF Wrapper

This code is for the "external" 32-bit ELF Crackme code.

This code takes unpacks a 64-bit binary, changes the CPU to long mode and hands off to it.

The source for this project is in the [`./spoilers-and-code/src/elf-binary-launcher`](./) directory.

## Dependencies

| Dependency Name | Description |
| -- | -- | 
| [`gcc`](https://gcc.gnu.org/) | Build tool used to compile C code.|
| (internal) [`elf-binary`](../elf-binary/README.md) | The 64-bit ELF binary (the core of the crackme; used as package contents - not directly needed). |
| (internal) [`elf-binary-patcher`](../elf-binary-patcher/README.md) / `ebp` | Used to modify and finalise ELF crackme binaries. This tool is used to create a missing file `payload.h` from the [internal 64-bit ELF binary](../elf-binary/README.md). |


## Compiling

Generate a new `payload.h` file using the [`elf-binary-patcher`](../elf-binary-patcher/README.md) / `ebp` module. You will need to build the [`64-bit elf binary`](../elf-binary/README.md) first. 

Assuming a `payload.h` file exists and dependencies are installed compiling this should be as simple as running the `scripts/build-launcher.sh` script. Note that the output from this build process is not stripped, so should not be shipped.

The python tools offer the following relevant/related commands

- `python -m cv build` - to build the whole CV. 
- `python -m cv build-crackme` - to build a _"ready-to-ship"_ ELF binary.
- `python -m cv build-crackme-launcher` - builds the launcher components of the CV CTF - this code.

You can use `ebp` ([`elf-binary-patcher`](../elf-binary-patcher/README.md)) is needed to generate a `payload.h` file, and can be used to strip/mangle this binary to make it _"ready-to-ship"_.