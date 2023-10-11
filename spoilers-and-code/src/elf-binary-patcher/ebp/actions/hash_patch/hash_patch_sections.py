# python imports
from struct import unpack
from enum import Enum
from typing import Sequence, TypeVar, Any, List
from re import compile as regex_compile
from logging import getLogger

# third-party imports
from pwnlib.elf import ELF
from elftools.elf.sections import Section
from elftools.construct import Struct, Container, Array, SLInt64

# project imports
from .sections.base import HashPatchSectionBase
from .sections import IncrementalIntegrity, XorToKnownValue, HashGenerator, InsertMurmur


## The @ref HashPatchSections `Self` type
SelfType = TypeVar('SelfType', bound='HashPatchSections')



## A list of special regions related to integrity hashing.
class SpecialHashActions(Enum):

    ## A generator section
    #  The data in this region is responsible for generating MurmurOAAT64 hashes. It needs to be patched 
    #  to know where virtual memory starts, and needs to know what parts of the software are "volatile"
    #  and need to be skipped from hashing.
    Generator = -1

    ## A section which requires an XOR mask for a known value.
    #  The data in this section wants an XOR mask that (when used with the current valid integrity hash)
    #  produces a known value.
    XorToKnownValue = -2

    ## A section which requires an hash injected for a known value.
    #  The data in this section wants an hash for a known value taken using a MummurOAAT hash seeded with 
    #  the current valid integrity hash - this should produce a hash we know ahead of time without disclosing
    #  the contents of the buffer.
    InsertMurmur = -3


## A decorator for methods responsible for converting meta data into a meaningful value.
#  In practise every conversion needs to convert the structure into bytes, and then usually unpack a tuple.
def meta_converter(func):

    ## The actual implementation we are wrapping.
    #  @param cls the type of class that is invoking this method.
    #  @param hash_patch_section_entry the section we are converting meta data from.
    #  @returns the value of the meta data once its been converted.
    def __implementation__(cls, hash_patch_section_entry:Container) -> Any:
        bytes_ = bytes(hash_patch_section_entry.meta)
        return func(cls, bytes_)

    # returns the implementation wrapped in a classmethod decorator.
    return classmethod(__implementation__)



## Object to hang `meta` data converters off.
class MetaConverter(object):

    ## Converts `meta` data into a string.
    #  @param cls the type of class that is invoking this method.
    #  @param meta the bytes that the meta field si composed of.
    #  @returns the value of the `meta` field interpretted as a string.
    @meta_converter
    def CString(cls, meta:bytes) -> str:
        meta_chars = meta.decode("ascii")
        return meta_chars.replace("\x00", "")


    ## Converts `meta` data into a unsigned long.
    #  @param cls the type of class that is invoking this method.
    #  @param meta the bytes that the meta field si composed of.
    #  @returns the value of the `meta` field interpretted as an unsigned long (8-byte unsigned integer).
    @meta_converter
    def UnsignedLong(cls, meta:bytes) -> int:
        value, = unpack("<Q", meta[:8])
        return value

    
    ## Converts `meta` data from a XorToKnown struct.
    #  @param cls the type of class that is invoking this method.
    #  @param meta the bytes that the meta field si composed of.
    #  @returns the value of the `meta` field interpretted as an xor_to_known_value struct.
    @meta_converter
    def XorToKnown(cls, meta:bytes) -> int:
        max_string_length = HashPatchSections.META_SIZE - (2 * HashPatchSectionBase.SIZE_OF_QWORD)
        required_value, order, sequence_bytes = unpack(f"<QQ{max_string_length}s", meta)
        sequence_string = sequence_bytes.decode("ascii")
        sequence = sequence_string.replace("\x00", "")
        return required_value, sequence, order


    ## Converts `meta` data from a InsertMurmur struct.
    #  @param cls the type of class that is invoking this method.
    #  @param meta the bytes that the meta field si composed of.
    #  @returns the value of the `meta` field interpretted as an xor_to_known_value struct.
    @meta_converter
    def InsertMurmur(cls, meta:bytes) -> int:
        max_string_length = HashPatchSections.META_SIZE - HashPatchSectionBase.SIZE_OF_QWORD - HashPatchSectionBase.SIZE_OF_DWORD
        size_of_buffer, order, buffer_bytes = unpack(f"<IQ{max_string_length}s", meta)
        size_of_buffer = min(size_of_buffer, max_string_length)
        buffer_value = buffer_bytes[:size_of_buffer]
        sequence_string = buffer_bytes[size_of_buffer:].decode("ascii")
        sequence = sequence_string.replace("\x00", "")
        return buffer_value, sequence, order


## A list of Hash Patch sections.
class HashPatchSections(list[HashPatchSectionBase]):
    
    ## The number of bytes to expect for the meta data field.
    META_SIZE = 256

    ## A regular expression to identify a hash patch section.
    HashActionSectionName = regex_compile(fr"^\.hash-patch\.(?P<filename>.+):(?P<line>[0-9]+)$")

    ## Logger used by this class instance.
    Log = getLogger("ebp.action.hash-patch")


    ## Gets a list of all the volatile offsets in the binary.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a list of volatile offsets in the binary.
    def volatile_offsets(self) -> List[int]:
        volatile_qwords = set( )
        volatile_qwords.update( *( s.volatile_offsets() for s in self ) )
        return sorted(volatile_qwords)


    ## Gets an instance of @ref HashPatchSections from the given @p elf ELF file.
    #  @param elf the ELF binary to generate a @ref HashPatchSections  from.
    #  @returns a @ref HashPatchSections from the given @p elf ELF file.
    @classmethod
    def fromElf(cls, elf:ELF) -> SelfType:

        sections = cls()

        for section in elf.iter_sections():

            if (cls.HashActionSectionName.match(section.name)):
                try:
                    descriptor = cls.parseSectionAction(section)
                    sections.append(descriptor)
                except RuntimeError as ex:
                    raise RuntimeError(f"{ex}; specified by {section.name}.") from ex

        return sections


    ## Parses a ".hash-patch." section in to a descriptor object.
    #  @param section the ELF section to parse a descriptor from.
    #  @returns a @ref HashPatchSectionBase object describing the content of the @p section.
    @classmethod
    def parseSectionAction(cls, section:Section) -> HashPatchSectionBase:
        
        section_data = Struct('hash_patch_section_entry',
            section.structs.Elf_addr('start_of_entry'),
            section.structs.Elf_addr('end_of_entry'),
            SLInt64('hash_action'),
            Array(cls.META_SIZE, section.structs.Elf_byte('meta'))
        ).parse( section.data() ) 
        
        if section_data.hash_action >= 0:
            return IncrementalIntegrity(
                section=section,
                start_address=section_data.start_of_entry,
                end_address=section_data.end_of_entry,
                sequence=MetaConverter.CString(section_data),
                order=section_data.hash_action,
            )

        elif section_data.hash_action == SpecialHashActions.Generator.value:
            return HashGenerator(
                section=section,
                start_address=section_data.start_of_entry,
                end_address=section_data.end_of_entry,
                volatile_qwords=MetaConverter.UnsignedLong(section_data)
            )
        elif section_data.hash_action == SpecialHashActions.XorToKnownValue.value:
            required_value, sequence, order = MetaConverter.XorToKnown(section_data)
            return XorToKnownValue(
                section=section,
                start_address=section_data.start_of_entry,
                end_address=section_data.end_of_entry,
                known_value=required_value,
                sequence=sequence,
                order=order,
            )
        elif section_data.hash_action == SpecialHashActions.InsertMurmur.value:
            buffer, sequence, order = MetaConverter.InsertMurmur(section_data)
            return InsertMurmur(
                section=section,
                start_address=section_data.start_of_entry,
                end_address=section_data.end_of_entry,
                expected_value=buffer,
                sequence=sequence,
                order=order,
            )
        else:
            raise RuntimeError(f"Unsupported hash-action identifier ({section_data.hash_action})")

