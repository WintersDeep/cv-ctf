
# python3 imports
from argparse import ArgumentParser, Namespace, Action
from typing import Any, Optional
from pathlib import Path

# project imports
from ebp.common import Elf
from ebp.actions.base import ActionBase
from ebp.common.algorithm import MersenneTwister
from .mt_sequence_encoders import MtSequenceCliEncoders



## Useful class to handle using a dictionary to provide CLI choices.
#  @remarks used to allow use of MtSequenceEncoders as a CLI option.
class DictAction(Action):

    ### Process values from the command line.
    # @param parser The ArgumentParser object which contains this action.
    # @param namespace The Namespace object that will be returned by parse_args(). Most actions add an attribute to this object using setattr().
    # @param values The associated command-line arguments, with any type conversions applied. Type conversions are specified with the type keyword argument to add_argument().
    # @param option_string The option string that was used to invoke this action. The option_string argument is optional, and will be absent if the action is associated with a positional argument.
    def __call__(self, parser:ArgumentParser, namespace:Namespace, 
            values:Any, option_string:Optional[str]=None) -> None:
        setattr(namespace, self.dest, self.choices.get(values, self.default))


## "Generate Mersenne Twister Sequence" action
#  Used to generate or preview mersenne twister sequences.
class GenerateMtSequenceAction(ActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "generate-mt-sequence"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "Generates and prints out a mersenne twister sequence."

    encoders = MtSequenceCliEncoders()


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `ElfBinaryPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument("seed", type=int, help="The seed to use to initialised the PRNG")
        argument_parser.add_argument("--count", "-c", type=int, default=100, help="The number of values to emit.")
        argument_parser.add_argument("--skip", "-s", type=int, default=0, help="The number of values in the sequence to jump over.")
        argument_parser.add_argument("--encode", "-e", action=DictAction, choices=cls.encoders, default=cls.encoders.one_per_line_hex,
            help="The encoder to use to output values")


    ## Invokes this action on an ELF file.
    #  This action will take protected strings from the binary and inject code to build the required strings.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = self.__class__.ExitSuccess

        self.log.info(f"Generating the Mersenne Twister sequence - {self.arguments.count} 32-bit integers after skipping {self.arguments.skip} for seed {self.arguments.seed}.")
        
        try:

            values = MersenneTwister.generate(self.arguments.seed, self.arguments.skip, self.arguments.count)
            if values: self.arguments.encode(self.arguments, values)

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = self.__class__.ExitRuntimeError
        
        return exit_code
