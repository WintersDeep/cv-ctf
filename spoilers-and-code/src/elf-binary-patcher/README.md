# Elf Binary Patcher (`ebp`)

Build tool used to manipulate and finalise ELF files in the CV CTF.

The source for this project is in the [`./spoilers-and-code/src/elf-binary-patcher`](./) directory.

## Dependencies

| Dependency Name | Description |
| -- | -- | 
| [`pwntools`](https://docs.pwntools.com/en/stable/) | Used to parse and modify ELF files. |
| (internal) [`elf-binary`](../elf-binary/README.md) | The 64-bit ELF binary (the core of the crackme; not directly needed, but is often the target of this application - "operated on"). |
| (internal) [`elf-binary-launcher`](../elf-binary-launcher/README.md) | The 32-bit ELF wrapped/launcher (the wrapping layer of the crack me; not directly needed, but depends on this project to finish it - "operated on")

## Setup

Consider creating a dedicated Python virtual environment for this tool.

```shell
# create a virtual environment
python -m venv venv

# update the pip package manager
venv/bin/python -m pip install --upgrade pip

# install this project (editable)
venv/bin/python -m pip install -e .
```

## Usage

Registers as top-level `ebp` python module; accessable from command line with usage as:

```shell
venv/bin/python -m ebp [-l {debug|info|warn|error}] { command... }
```
The following commands are available (use `python -m ebp {command} --help` for information about arguments)

| Command | Description |
| ---- | ---- |
| `generate-hidden-string` | Creates the values needed to generate "hidden" or sensitive strings in the binary - given the target string, the command will return a random PRNG seed value, and the bytes that should be XOR'd against that seed to generate the string. You can specify the PRNG seed value if a specific one is required. This is useful for embedding defaults in at development time. |
| `generate-mt-sequence` | Generates the sequence of numbers that will be yielded by the embedded PRNG when initialised with the given seed value. Used for development and testing (the PRNG might not be 100% standards complient because its funnier that way, and having offline reference to the explict implementation is useful). |
| `protect-strings` | Injects assembly instructions to build protected strings in an [`internal 64-bit elf-binary`](../elf-binary/README.md). These are defined with the `ALLOC_PROTECTED_STRING` or `ASSIGN_PROTECTED_STRING` macro's in that source base which will reserve `.text` space with `NOP` instructions for this assembly. | 
| `hash-patch` | Finalises the integrity checking mechanisms in an [`internal 64-bit elf-binary`](../elf-binary/README.md); generates a random initialisation vector and calculates what the resulting integrity hashes should be - patches the sofware where these values are used / depended on. These values are defined with the following constants; `INTEGRITY_HASH`, `INTEGRITY_SEED`, `XOR_MASK_FOR_KNOWN_VALUE`, `EXPECTED_MURMUR_HASH`, and used with the following macros; `CONTAINS_INTEGRITY_HASH`, `CONTAINS_INTEGRITY_GENERATOR`, `REQUIRES_INTEGRITY_XOR_TO_KNOWN`, `REQUIRES_INTEGRITY_MURMUR_HASH`. **IT IS IMPORTANT THAT THIS IS THE LAST PATCH APPLIED TO THE BINARY; FURTHER CHANGES TO THE INTERNAL BINARY TEXT SECTION AFTER THIS PROCESS COMPLETES WILL BREAK INTEGRITY**.|
| `write-payload-header` | Given a patched [`internal 64-bit elf-binary`](../elf-binary/README.md), generates a `payload.h` header file that can be used to build the [`external 32-bit elf binary`](../elf-binary-launcher/README.md).
| `strip-binary` | Used to strip all non-essential data from a built [`external 32-bit elf binary`](../elf-binary-launcher/README.md) binary, and mangles its ELF header for good measure.|