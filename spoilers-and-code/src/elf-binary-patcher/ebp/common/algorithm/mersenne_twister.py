# python imports
from typing import TypeVar, Iterator
from struct import pack


## The @ref MersenneTwister `Self` type
SelfType = TypeVar('SelfType', bound='MersenneTwister')


## Mersenne Twister PRNG
#
# Simple PRNG used for predictable random number generation. We could have relied on an open 
# source implementation but they usually come with features we don't need and may use 
# alternate seeding mechanics - we need to be able to reproduce values created by this 
# generator in the binary, so it helps to be in full control of things.
#
# Base on; [Wikipedia's documentation for MT19937](https://en.wikipedia.org/wiki/Mersenne_Twister)
class MersenneTwister(object):


    ## The size of the internal PRNG's state 
    #  "n: degree of recurrence" in documentation.
    MT19937_STATE_SIZE = 624

    ## The size of a word in bits
    #  @remarks could consider using 64 in future - see MT19937-64 on wikipedia.
    #     to relevant parameters - would also need to change internal data types.
    WORD_SIZE = 32

    ## Masks to ensure generated values fit in word size.
    #  Operates with long values (8 bytes in context), this is used to discard overflow.
    WORD_MASK = (1 << WORD_SIZE) - 1

    ## The most signficant bit of the word.
    BITMASK_32B_MSB = 1 << (WORD_SIZE - 1)

    ## All the other bits of the word
    BITMASK_32B_317LSB = ~BITMASK_32B_MSB



    ## MT19937 'a' component
    #  Coefficients of the rational normal form twist matrix
    MT19937_A = 0x9908B0DF

    ## MT19937 'b' component
    #  TGFSR(R) tempering bitmasks
    MT19937_B = 0x9d2c5680

    ## MT19937 'c' component
    #  TGFSR(R) tempering bitmasks
    MT19937_C = 0xefc60000

    ## MT19937 'f' component
    #  The constant f forms another parameter to the generator, though not part of the algorithm proper.
    #  @remarks The value for f for MT19937 is 1812433253
    MT19937_F = 0x6C078965

    ## MT19937 'l' component
    # Additional Mersenne Twister tempering bit shifts#masks
    MT19937_L = 0x00000012

    ## MT19937 'm' component
    #  Middle word, an offset used in the recurrence relation defining the series: x, 1 <= m < n
    MT19937_M = 0x0000018d

    ## MT19937 's' component
    #  TGFSR(R) tempering bit shifts
    MT19937_S = 0x00000007

    ## MT19937 't' component
    #  TGFSR(R) tempering bit shifts
    MT19937_T = 0x0000000f

    ## MT19937 'u' component
    #  Additional Mersenne Twister tempering bit shifts#masks
    MT19937_U = 0x0000000b


    ## Shortcut for generating a predefined sequence.
    #  @param cls the type of class that is invoking this method.
    #  @param seed the value to seed the generator with.
    #  @param skip the number of values to skip.
    #  @param count the number of values to generate.
    @classmethod 
    def generate(cls, seed:int, skip:int, count:int) -> list[int]:
        mt = cls(seed)        
        for _ in range(skip):  mt.next_uint32()
        values = [ mt.next_uint32() for _ in range(count) ]
        return values


    ## Instanciates a new @ref MersenneTwister object.
    #  @param cls the type of object that is invoking this method.
    #  @param seed the value used to intialise the PRNG state
    def __init__(cls, seed:int=0) -> SelfType:

        cls.index = 1
        cls.state = [ seed ] * cls.__class__.MT19937_STATE_SIZE

        while(cls.index < cls.__class__.MT19937_STATE_SIZE):
            
            v = cls.state[cls.index -1]

            cls.state[cls.index] = (cls.__class__.MT19937_F * (
                v ^ (v >> (cls.__class__.WORD_SIZE - 2))
            ) + cls.index) & cls.__class__.WORD_MASK

            cls.index += 1


    ## "Twist" internal state
    #  Progresses the internal state when all current values have been consumed.
    #  @param cls the type of object that is invoking this method.
    def _twist(cls) -> None:

        for index in range(0, cls.__class__.MT19937_STATE_SIZE):
            next_index = (index + 1) % cls.__class__.MT19937_STATE_SIZE
            take_index = (index + cls.__class__.MT19937_M) % cls.__class__.MT19937_STATE_SIZE

            x = (cls.state[index] & cls.__class__.BITMASK_32B_MSB) | \
                (cls.state[next_index] & cls.__class__.BITMASK_32B_317LSB)

            xA = x >> 1

            cls.state[index] = cls.state[take_index] ^ (
                xA ^ cls.__class__.MT19937_A if x % 2 == 1 else xA
            )
        
        cls.index = 0

    ## Generates the next unsigned 32bit number in the PRNGs sequence.
    #  @param cls the type of object that is invoking this method.
    #  @returns the next number from the PRNG's random sequence.
    def next_uint32(cls) -> int:
        
        if cls.index >= cls.__class__.MT19937_STATE_SIZE:
            cls._twist()

        y = cls.state[cls.index]
        y = y ^ ((y >> cls.__class__.MT19937_U) & cls.__class__.WORD_MASK)
        y = y ^ ((y << cls.__class__.MT19937_S) & cls.__class__.MT19937_B)
        y = y ^ ((y << cls.__class__.MT19937_T) & cls.__class__.MT19937_C)
        y = y ^ (y >> cls.__class__.MT19937_L)

        cls.index += 1

        return y & cls.__class__.WORD_MASK
    



### Encoders to take the MT sequence and present the value in a defined manner.
class MtSequenceEncoders(object):

    ## Prints the given sequence, one value at a time as a decimal value.
    #  @param cls the type of object that is invoking this method.
    #  @param generator the generator that will yield the sequence values.
    #  @returns the string value used to express the sequence in the requested format.
    @classmethod
    def one_per_line_dec(cls, generator:Iterator[int]) -> str:
        return "\n".join( map(str, generator ))


    ## Prints the given sequence, one value at a time as a hexadecimal value.
    #  @param cls the type of object that is invoking this method.
    #  @param generator the generator that will yield the sequence values.
    #  @returns the string value used to express the sequence in the requested format.
    @classmethod
    def one_per_line_hex(cls, generator:Iterator[int]) -> str:
        hex = lambda v: f"0x{v:08x}"
        return "\n".join( map(hex, generator ))


    ## Prints the given sequence as a C `unsigned int` array.
    #  @param cls the type of object that is invoking this method.
    #  @param variable_name name of the c variable to build the array on.
    #  @param generator the generator that will yield the sequence values.
    #  @param tab_size the number of spaces to use for a tab in output.
    #  @param items_per_line number of array elements per c source line.
    #  @returns the string value used to express the sequence in the requested format.
    @classmethod
    def c_uint_array(cls, variable_name:str, generator:Iterator[int], tab_size:int = 4, items_per_line:int=16) -> str:
        
        lines = [f"unsigned int {variable_name}[] = {{"]
        tab = " " * tab_size
        leading_comma = ""
        
        for index, v in enumerate(generator):
            lines[-1] += leading_comma
            if index % items_per_line == 0: 
                lines.append(tab)
            lines[-1] += f"0x{v:08x}"            
            leading_comma = ", "

        lines.append("}")

        return "\n".join(lines)


    ## Prints the given sequence as a C `unsigned char` array.
    #  @remarks NOTE that this is never invoked directly - instead a wrapper is provided that
    #     handles converting the MT int32 values into a steam of 4 single bytes first.
    #  @param cls the type of object that is invoking this method.
    #  @param variable_name name of the c variable to build the array on.
    #  @param generator the generator that will yield the sequence values.
    #  @param tab_size the number of spaces to use for a tab in output.
    #  @param items_per_line number of array elements per c source line.
    #  @returns the string value used to express the sequence in the requested format.
    @classmethod
    def _c_char_array(cls, variable_name:str, generator:Iterator[int], tab_size:int = 4, items_per_line:int=32) -> str:
        
        lines = [f"unsigned char {variable_name}[] = {{"]
        tab = " " * tab_size
        leading_comma = ""
        
        for index, v in enumerate(generator):
            lines[-1] += leading_comma
            if index % items_per_line == 0: 
                lines.append(tab)
            lines[-1] += f"0x{v:02x}"            
            leading_comma = ", "

        lines.append("}")

        return "\n".join(lines)

    ## Prints the given sequence as a C `unsigned char` array with each MT uint32 being interpretted as a little endian value.
    #  @param cls the type of object that is invoking this method.
    #  @param variable_name name of the c variable to build the array on.
    #  @param generator the generator that will yield the sequence values.
    #  @param tab_size the number of spaces to use for a tab in output.
    #  @param items_per_line number of array elements per c source line.
    #  @returns the string value used to express the sequence in the requested format.
    @classmethod
    def c_char_array_le(cls, variable_name:str, generator:Iterator[int], tab_size:int = 4, items_per_line:int=32) -> str:
        
        def char_generator_for_little_endian():
            for uint32 in generator:
                yield from pack("<I", uint32)

        return cls._c_char_array(variable_name, char_generator_for_little_endian(), tab_size, items_per_line)


    ## Prints the given sequence as a C `unsigned char` array with each MT uint32 being interpretted as a big endian value.
    #  @param cls the type of object that is invoking this method.
    #  @param variable_name name of the c variable to build the array on.
    #  @param generator the generator that will yield the sequence values.
    #  @param tab_size the number of spaces to use for a tab in output.
    #  @param items_per_line number of array elements per c source line.
    #  @returns the string value used to express the sequence in the requested format.   
    @classmethod
    def c_char_array_be(cls, variable_name:str, generator:Iterator[int], tab_size:int = 4, items_per_line:int=32) -> str:
        
        def char_generator_for_big_endian():
            for uint32 in generator:
                yield from pack(">I", uint32)

        return cls._c_char_array(variable_name, char_generator_for_big_endian(), tab_size, items_per_line)