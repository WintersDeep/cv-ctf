# python imports
from struct import pack
from random import randint
from typing import Iterator, TypeVar, Optional

# project imports
from ebp.common.algorithm import MersenneTwister


## The @ref HiddenString `Self` type
HiddenStringType = TypeVar('HiddenStringType', bound='HiddenString')


## Object which handles representation of a hidden string
class HiddenString(object):


    ## Wraps a mersenne twister to provide an interator of bytes (rather than uint32)
    #  UINT32 is converted into bytes using little endian such as it would be seen in memory.
    #  @param cls the type of class that is invoking this method.
    #  @param mersenne_twister the PRNG to wrap.
    #  @returns an iterator of integer byte values derived from the PRNG.
    def mersenne_twister_byte_iterator(cls, mersenne_twister:MersenneTwister) -> Iterator[int]:
        while 1:
            uint32 = mersenne_twister.next_uint32()
            yield from pack("<I", uint32)

    ## XORS the given byte squence against the current MT state.
    #  @param self the instanec of the object that is invoking this method.
    #  @param byte_sequence the sequence of bytes to XOR against the MT sequence.
    #  @returns the input bytes XOR'd against the MT sequence.
    def mt_xor_byte_sequence(self, byte_sequence:Iterator[int]) -> list[int]:
        mt_byte_iterator = self.mersenne_twister_byte_iterator(self.mt)
        return [ b ^ next(mt_byte_iterator) for b in byte_sequence ]


    ## Creates a new instance of this object.
    #  @param self the instance of the object that is invoking this method.
    #  @param hidden_string the hidden string to set.
    #  @param long_seed the seed to use to embed the hidden string (or NULL for random).
    def __init__(self, hidden_string:str, long_seed:Optional[int] = None) -> HiddenStringType:
        self.long_seed = long_seed or randint(0x0000000000000000, 0xFFFFFFFFFFFFFFFF)
        self.short_seed = (self.long_seed >> 32) ^ (self.long_seed & 0xffffffff)
        self.mt = MersenneTwister(self.short_seed)        
        self.xor_bytes = self.mt_xor_byte_sequence(hidden_string.encode("ascii") + b"\0")
        self.raw = hidden_string

    ## Gets the hidden string mask as a byte string
    #  @param self the instance of the object that is invoking this method.
    #  @returns byte string interpretation of the XOR mask.
    @property
    def mask_byte_string(self):
        return bytes(self.xor_bytes)

    ## Gets the hidden string mask as a c-style byte string definition
    #  @param self the instance of the object that is invoking this method.
    #  @returns a c-style byte string interpretation of the XOR mask.
    @property
    def mask_c_string(self):
        character_values = map(lambda b: f"\\x{b:02x}", self.xor_bytes)
        return "".join(character_values)