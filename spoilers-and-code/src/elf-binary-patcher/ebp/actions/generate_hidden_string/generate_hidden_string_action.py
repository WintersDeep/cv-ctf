
# python3 imports
from argparse import ArgumentParser, Namespace
from random import randint

# project imports
from ebp.common import HiddenString
from ebp.actions.base import ActionBase


## "Generate Hidden Strings" action
#  Use to generate values that are used to embed secrets in the binary.
class GenerateHiddenStringAction(ActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "generate-hidden-string"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "Generates values needed to embed a hidden string in the crackme."


    ## Determines the seed long value to embed in the software.
    #  If the user sets a long seed this is validated, but otherwise used directly.
    #  If the user gives a short seed this is converted into a long seed using a random fragment.
    #  If the user gives neither an entirely random long seed is generated.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the CLI provided arguments given to the application.
    #  @returns The long seed value to use in the software.
    def determine_long_seed(self, arguments:Namespace) -> int:

        max_size = 0
        test_seed = 0
        long_seed = 0

        if arguments.long_seed:
            max_size = 0xffffffffffffffff
            test_seed = arguments.long_seed
            long_seed = arguments.long_seed        
        else:
            max_size = 0xffffffff
            fragment = randint(0x00000000, 0xffffffff)
            test_seed = arguments.seed or randint(0x00000000, 0xffffffff)
            long_seed = fragment << 32 | (fragment ^ test_seed)
        
        if test_seed < 0 or test_seed != test_seed & max_size:
            raise ValueError(f"Seed value {test_seed} provided on CLI was not in valid range for option (0-{max_size}).")

        return long_seed
    

    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `ElfBinaryPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:

        argument_parser.add_argument("hidden_string", metavar="hidden-string", type=str, help="The hidden string that you want to embed.")

        seed_group = argument_parser.add_mutually_exclusive_group()
        seed_group.add_argument("--seed", "-s", type=int, help="The literal seed used to initialise the PRNG which disguises the embedded hidden string (usually should be omitted to be random).")
        seed_group.add_argument("--long-seed", "-ls", type=int, help="The fragmented seed used to initialised the PRNG which disguises the embedded hidden string (usually should be omitted to be random).")    


    ## Invokes this action on an ELF file.
    #  This action will take protected strings from the binary and inject code to build the required strings.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = self.__class__.ExitSuccess

        self.log.info(f"Generating the hidden string.")
        
        try:


            long_seed = self.determine_long_seed(self.arguments)
            definitions = HiddenString(self.arguments.hidden_string, long_seed)

            to_hex_array = lambda b: f"0x{b:02x}"
            to_c_string = lambda b: f"\\x{b:02x}"

            print(f"      Seed (Literal): {definitions.short_seed} / 0x{definitions.short_seed:08x}")
            print(f"     Seed (Fragment): {definitions.long_seed} / 0x{definitions.long_seed:016x}")
            print(f"    Mask [hex-array]: {', '.join(map(to_hex_array, definitions.xor_bytes))}")
            print(f"         [ c-string]: {''.join(map(to_c_string, definitions.xor_bytes))}")


        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = self.__class__.ExitRuntimeError
        
        return exit_code
