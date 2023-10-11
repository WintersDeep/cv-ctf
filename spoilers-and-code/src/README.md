# Project Descriptions

High level description of the projects in this directory to aid navigation.

| Project | Description | 
| ---- | ---- |
| [`cv-builder`](./cv-builder/README.md) | Python utility to build / manipulate the CV content as a whole or one of its various components.|
| [`elf-binary`](./elf-binary/README.md) | The core 64-bit code for the ELF binary - the core of the crackme / flag4. |
| [`elf-binary-launcher`](./elf-binary-launcher/README.md) | The 32-bit code that wraps/launches the 64-bit code in the  [`elf-binary`](./elf-binary/README.md) |
| [`elf-binary-patcher`](./elf-binary-patcher/README.md) | Python utility to build / manipulate the various ELF binary components; does things such as building protected strings, patching the memory integrity processes, or packaging the 64-bit code for use in the 32-bit wrapper. |
| [`pdf-patcher`](./pdf-patcher/README.md) | Python utility to build / manipulate PDF content. Does things like generating the version layered document, or injecting the second flag QR code. |