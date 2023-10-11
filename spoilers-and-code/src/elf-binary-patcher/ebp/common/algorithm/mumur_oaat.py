# python3 imports
from typing import Iterator, TypeVar


## The @ref MurmurOaat64 `Self` type
SelfType = TypeVar('SelfType', bound='MurmurOaat64')


## MurmurOaat64-ish algorithm
#  Used for basic binary hashing as an integrity check.
class MurmurOaat64(object):


    ## Instanciates a new @ref MurmurOaat64 object.
    #  @param self the instance of the object that is invoking this method.
    #  @param seed the value used to intialise the hash state
    def __init__(self, seed:int) -> SelfType:
        self.state = seed


    ## Applies a single byte to the hash state.
    #  @param self the instance of the object that is invoking this method.
    #  @param byte_ the byte to apply to the hash state.
    def consume_byte(self, byte_:int) -> None:
        self.state ^= byte_
        self.state *= 0x5bd1e9955bd1e995
        self.state &= 0xffffffffffffffff
        self.state ^= self.state >> 0x2f
    

    ## Applies a series of bytes to the hash.
    #  @param self the instance of the object that is invoking this method.
    #  @param iterator iterator to consume bytes from - consumes until the iterator ends.
    def consume(self, iterator:Iterator[int]) -> None:
        for byte_ in iterator:
            self.consume_byte(byte_)
    

    ## Gets the current value of the hash.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the current state / hash.
    def __int__(self) -> int:
        return self.state




    