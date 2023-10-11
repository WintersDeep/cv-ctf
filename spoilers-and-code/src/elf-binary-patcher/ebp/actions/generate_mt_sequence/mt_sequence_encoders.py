
# python imports
from argparse import Namespace
from struct import pack
from typing import Iterator

from ebp.common.algorithm.mersenne_twister import MtSequenceEncoders


### Encoders to take the MT sequence and present the value in a defined manner.
class MtSequenceCliEncoders(dict):


    ## Creates a new instanec of this class.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the new instance of this object type.
    def __init__(self) -> dict:
        super().__init__()
        self['one-per-line-dec'] = self.one_per_line_dec
        self['one-per-line-hex'] = self.one_per_line_hex
        self['c-char-array-le'] = self.c_char_array_le
        self['c-char-array-be'] = self.c_char_array_be
        self['c-uint-array'] = self.c_uint_array


    ## Prints the given sequence, one value at a time as a decimal value.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments the arguments provided by the user on the CLI.
    #  @param generator the generator that will yield the sequence values.
    def one_per_line_dec(self, arguments:Namespace, generator:Iterator[int]) -> None:
        print( MtSequenceEncoders.one_per_line_dec(generator) )


    ## Prints the given sequence, one value at a time as a hexadecimal value.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments the arguments provided by the user on the CLI.
    #  @param generator the generator that will yield the sequence values.
    def one_per_line_hex(self, arguments:Namespace, generator:Iterator[int]) -> None:
        print( MtSequenceEncoders.one_per_line_hex(generator) )



    ## Prints the given sequence as a C `unsigned int` array.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments the arguments provided by the user on the CLI.
    #  @param generator the generator that will yield the sequence values.
    def c_uint_array(self, arguments:Namespace, generator:Iterator[int]) -> None:
        print(f"/// mersenne-twister sequence for seed {arguments.seed}")
        if(arguments.skip): print(f"//  @note: {arguments.skip} initial values skipped/discarded.")
        print(MtSequenceEncoders.c_uint_array( f"mt_seed_{arguments.seed:08x}_values", generator ))


    ## Prints the given sequence as a C `unsigned char` array with each MT uint32 being interpretted as a little endian value.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments the arguments provided by the user on the CLI.
    #  @param generator the generator that will yield the sequence values.
    def c_char_array_le(self, arguments:Namespace, generator:Iterator[int]) -> None:
        print(f"/// mersenne-twister sequence for seed {arguments.seed} (uint32, little-endian encoded)")
        if(arguments.skip): print(f"//  @note: {arguments.skip} initial values skipped/discarded.")
        print(MtSequenceEncoders.c_char_array_le( f"mt_seed_{arguments.seed:08x}_values", generator ))


    ## Prints the given sequence as a C `unsigned char` array with each MT uint32 being interpretted as a big endian value.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments the arguments provided by the user on the CLI.
    #  @param generator the generator that will yield the sequence values.    
    def c_char_array_be(self, arguments:Namespace, generator:Iterator[int]) -> None:
        print(f"/// mersenne-twister sequence for seed {arguments.seed} (uint32, big-endian encoded)")
        if(arguments.skip): print(f"//  @note: {arguments.skip} initial values skipped/discarded.")
        print(MtSequenceEncoders.c_char_array_be( f"mt_seed_{arguments.seed:08x}_values", generator ))
