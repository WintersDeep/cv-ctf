# project imports
from .base import VolatileLocation, VolatileLocationList
from .patch_protected_strings import PatchProtectedStringsAction
from .hash_patch import HashPatchAction
from .generate_mt_sequence import GenerateMtSequenceAction
from .generate_hidden_string import GenerateHiddenStringAction
from .write_payload_header import WritePayloadHeaderAction
from .strip_binary import StringBinaryAction

# third-party imports
from pwnlib.elf import ELF

## A list of actions this tool can perform.
available_actions = [
    GenerateHiddenStringAction,
    GenerateMtSequenceAction,
    PatchProtectedStringsAction,
    HashPatchAction,
    WritePayloadHeaderAction,
    StringBinaryAction
]


## Gets a list of regions in the binary that various actions are identifying as volatile
#  Volatile regions are likely to change; it is also a good idea to ignore data that contains NOP's (0x90).
#  @param elf the ELF binary to query for volatile regions.
#  @returns a list of volatile regions in the binary.
def get_volatile_regions(elf:ELF) -> VolatileLocationList:
    from .base import InOutPatchActionBase
    volatile_regions = VolatileLocationList()
    for cls in available_actions:
        if issubclass(cls, InOutPatchActionBase):
            action_specific_volatility = cls.volatile_locations(elf)
            volatile_regions.extend(action_specific_volatility)
    return volatile_regions