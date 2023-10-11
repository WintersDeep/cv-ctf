# python imports
from typing import TypeVar, Iterator
from struct import pack

# third-party imports
from elftools.elf.sections import Section

#project imports
from .incremental_integrity_base import IncrementalIntegrityBase

## The @ref XorToKnownValue `Self` type
SelfType = TypeVar('SelfType', bound='XorToKnownValue')


## Represents an XOR to known value.
#  Used to insert a QWORD that will XOR with the current (valid) integrity hash to produce a known good value.
#  This should be used creatively to do something with knowledge that the value might be incorrect if tampering
#  was detected.
class XorToKnownValue(IncrementalIntegrityBase):

    ### The magic value that will be replaced by a post build tool with an XOR mask (against current hash) to produce a known value 
    ##  This hash QWORD is considered volatile and will be omitted from hash checking.
    XOR_MASK_FOR_KNOWN_VALUE = pack("<Q", 0x5afe70bec0d3ab1e)

    ## Creates a new instance of the @ref XorToKnownValue object.
    #  @param self the instance of the object that is invoking this method.
    #  @param section the section this descriptor was built from.
    #  @param start_address start of region that contains the XOR mask requirement.
    #  @param end_address end of the region that contains the XOR mask requirement.
    #  @param sequence the name of the sequence that this check belongs to.
    #  @param order the order of the check in the sequence (numbers do not have to be consecutive, or unique).
    #  @param known_value the known value that is required.
    def __init__(self, section:Section, start_address:int, end_address:int, sequence:str, order:int, known_value:int) -> SelfType:
        super().__init__(section, start_address, end_address, sequence, order)
        self.known_value = known_value

    ## Returns an enumerator of offsets into this region of scoped memory that look like places to inject the required XOR mask.
    #  @param self the instance of the object that is invoking this method.
    #  @returns an enumerator of virtual memory addresses which contain the integrity seed placeholder.
    def xor_mask_offsets(self) -> Iterator[int]:
        yield from self.locate_byte_sequence_in_scoped_memory(self.XOR_MASK_FOR_KNOWN_VALUE)
        return
        yield


    ## Returns an enumerator of offsets which should not be part of the integrity checking.
    #  By default this is just going to return the location of INTEGRITY_HASH usage - however some section types might need to override this
    #  and add more (for instance if we want to XOR the current hash against something to get a known value, that XOR value will need to be 
    #  volatile too).
    #  @param self the instance of the object that is invoking this method.
    #  @returns an enumerator of virtual memory addresses which contain 8-byte QWORDS that should not be integrity checked.
    def volatile_offsets(self) -> Iterator[int]:
        yield from super().volatile_offsets()
        yield from self.xor_mask_offsets()
        return
        yield