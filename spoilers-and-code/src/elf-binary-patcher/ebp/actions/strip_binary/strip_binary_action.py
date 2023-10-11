

# python3 imports
from argparse import ArgumentParser
from typing import List
from pathlib import Path

# third-party imports
from pwnlib.elf import ELF
from elftools.elf.sections import Section

# project imports
from ebp.actions.base import InOutPatchActionBase, VolatileLocationList


## String Binary Action.
#  The strip binary action removes all the segments and sections from the binary that we no longer need / want.
#  This is generally one of the last actions performed on the final binary.
class StringBinaryAction(InOutPatchActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "strip-binary"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "guts everything out of the binary that we don't need/want." 


    ## Returns a list of locations that are going to be re-written/changed by this action.
    #  This is needed as some actions reflectively pull data from the binary and need to pick locations that
    #  are not going to be subject to change.
    #  @param cls the type of class invoking this method.
    #  @param elf the elf to locate volatile regions in.
    #  @returns a list of volatile regions in the binary.
    @classmethod
    def volatile_locations(cls, elf:ELF) -> VolatileLocationList:        
        # @tdb don't current need to worry about this - its done after any active patching.
        protected_string_volatiles = []
        return protected_string_volatiles


    def get_section(self) -> Section:
        
        elf = self.arguments.elf
        
        section_name = ".text" # make this an option if required.
        section = elf.get_section_by_name(section_name)

        if not section: 
            raise RuntimeError(f"Failed to locate executable section '{section_name}'.")

        return section


    ## Invokes this action on an ELF file.
    #  This action will take protected strings from the binary and inject code to build the required strings.
    #  @param elf the ELF file this action should operate on.
    #  @returns patch process exit code.
    def __call__(self) -> None:

        exit_code = self.__class__.ExitSuccess

        try:
            self.log.info(f"starting to strip binary '{self.arguments.elf.path}'.")
            
            elf = self.arguments.elf
            
            header = elf.header.copy()
            section = self.get_section()
            entry_offset = elf.entry - section.header.sh_addr

            if entry_offset < 0 or entry_offset > section.header.sh_size:
                raise RuntimeError("ELF entry address is not in target section.")
            
            segment = elf.get_segment_for_address(elf.entry).header.copy()

            header['e_phnum'] = 0x0001                                                      # we only want one program header
            header['e_phoff'] = elf.structs.Elf_Ehdr.sizeof()                               # and the program header table starts immediately after the ELF header.
                                                                                            
                                                                                            # NUKE THE SECTION HEADERS
            header['e_shentsize'] = 0xffff                                                  # because why not; huge section header size
            header['e_shnum']     = 0x0000                                                  # because there are no sections.
            header['e_shoff']     = 0x0000                                                  # so we don't need to worry about the section offset.
            header['e_shstrndx']  = 0x0000                                                  # nor the section strings table


            binary_start = header['e_phoff'] + elf.structs.Elf_Phdr.sizeof()                # calculate where the .text section starts

            header['e_entry'] = segment['p_vaddr'] + binary_start + entry_offset            # update the binary entry point...
            header.e_ident['EI_DATA'] = 'ELFDATA2MSB'                                       # change the endianess of the header to big, (theres no such thing as x86 big - it doesn't matter but can mess with debug tools)

            segment['p_offset'] = 0                                                         # recalculate the program header offset to the start of the segment.
            segment['p_filesz'] = binary_start + section.header['sh_size']                  # adjust the .text file size to include the header.
            segment['p_memsz'] = segment['p_filesz']                                        # sync memory and file sizes.

            elf_bytes = b"".join([                                                          # write the new file.
                elf.structs.Elf_Ehdr.build(header),
                elf.structs.Elf_Phdr.build(segment),
                section.data()
            ])

            with self.arguments.out_file.open("wb") as output_handle:
                output_handle.write(elf_bytes)

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = self.__class__.ExitRuntimeError

        return exit_code