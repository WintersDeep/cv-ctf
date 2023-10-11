# python3 imports
from typing import Iterable, Iterator

# python imports
from typing import TypeVar

# third-party imports
from pwnlib.elf import ELF
from elftools.elf.sections import Section
from elftools.construct import Struct, Container, Array


## The @ref ProtectedString `Self` type
SelfType = TypeVar('SelfType', bound='ProtectedString')

ASM_NOP = 0x90

## Contains the contents of a `.protected-string-entry.N` ELF section.
#  This is a custom structure that is defined in the `elf-binary` source and contains information
#  about a static string that we want to embed in the ELF binary in an non-transparent manner.
class ProtectedString(object):


    ## The prefix used to record where protected strings are required.
    SectionNamePrefix:str = ".protected-string-entry"


    ## The maximum number of bytes we allow between a protected strings recorded address, and the actual reservation.
    MaximumAsmPreamble:int = 0x10


    ## Gets an iterator of @ref ProtectedString sections from the give @p elf.
    #  @param elf the ELF binary to extract @ref ProtectedString sections from.
    #  @returns an iterator of sections extracted from the ELF file.
    @classmethod
    def fromElf(cls, elf:ELF) -> Iterator[SelfType]:
        for section in elf.iter_sections():
            if section.name.startswith(cls.SectionNamePrefix):
                yield cls.fromSection(section)
        return
        yield
        

    ## Converts a `elftools.elf.sections.Section` into an @ref ProtectedString.
    #  Note that there is no error handling here - we assume the section is conformant to spec and 
    #  behaved (ironic eh?) - this script is only even inteded to run on trusted data.
    #  @param section the section to convert into a @ref ProtectedString.
    #  @returns ProtectedString interpretation of the data.
    @classmethod
    def fromSection(cls, section:Section) -> SelfType:

        section_struct = Struct('protected_string_section_entry',
            section.structs.Elf_addr('reservation_virtual_memory_address'),
            section.structs.Elf_word('reservation_size')
        )

        section_data = section.data()
        header_size = section_struct.sizeof()
        section_header = section_struct.parse( section.data() ) 


        return cls(section, section_header, section_data[header_size:])


    ## Locates and verifies the virtual memory address for the protected string.
    #  The address reported by sections for protected strings is always going to be a little offset - this is because its
    #  based on a label which is placed prior to an empty ASM block. Whilst the ASM block itself is empty GCC will insert 
    #  some instructions between the label and the ASM block to store/protect registers and move the target into RBX, so 
    #  the actual reservation space (a series of NOPs) will be some bytes behind the given address. This code searches the
    #  bytes immediately after the given address to find the actual reservation space. We expect the reservation to be found
    #  within N bytes of the recorded address; if we can't find a suitable candidate in this space we raise an error. 
    #  @remarks in context N is defined by @ref PatchProtectedStrings::MaximumAsmPreamble
    #  @param section_data the section we are trying to find the reservation space for.
    #  @returns the actual address the reservation begins or -1 if the location cannot be found.
    def locate_virtual_memory_address(self) -> int:

        current_offset = 0
        reservation_size = self.reservation_size
        virtual_memory_address_needle = self.virtual_memory_address_label
        search_size = ProtectedString.MaximumAsmPreamble + reservation_size

        virtual_memory = self.elf.read(virtual_memory_address_needle, search_size)

        while current_offset < ProtectedString.MaximumAsmPreamble:

            if virtual_memory[current_offset] == ASM_NOP:

                # if the current offset is a NOP - check we have enough NOP's afterwards.
                for verify_offset in range(current_offset, current_offset + reservation_size):
                    if virtual_memory[verify_offset] != ASM_NOP:
                        break 
                else: # if we managed to complete the above loop without finding a non-NOP - we have our reserved space
                    virtual_memory_address_needle += current_offset
                    return virtual_memory_address_needle
                    
                # if we got here we enountered a non-NOP @ verify_offset - carry on the search for the reserve space from this location 
                current_offset = verify_offset    

            current_offset += 1

        return -1

    ## Instanciates a new @ref ProtectedString object.
    #  @param self the instance of the object that is invoking this method.
    #  @param section the `elftools.elf.sections.Section` object the data was read from.
    #  @param data the data that was extracted from this section.
    def __init__(self, section:Section, data:Container, expected_string:bytes) -> SelfType:
        self._section = section
        self._data = data
        self.expected_string = expected_string
        self.virtual_memory_address = self.locate_virtual_memory_address()

    ## Determines if the virtual memory for this string was found.
    #  @param self the instance of the object that is invoking this method.
    #  @returns True if the memory reservation was found else False.
    def virtual_memory_found(self) -> bool:
        return self.virtual_memory_address >= 0

    ## The ELF file that contained this objects source section.
    @property
    def elf(self) -> ELF:
        return self._section.elffile


    ## The ELF section this object object was created from.
    @property
    def section(self) -> Section:
        return self._section


    ## The approximate location of the virtual memory that needs to be patched to
    #  include the protected string. This will never be 100% and a search of the 
    #  memory immediately behind this address will need to be performed.
    #  This is where the label was inserted.
    @property
    def virtual_memory_address_label(self) -> int:
        return self._data.reservation_virtual_memory_address


    ## The size of the reserved space. Used for validation purposes.
    @property
    def reservation_size(self) -> int:
        return self._data.reservation_size