# python3 imports
from typing import Iterator

# project imports
from .base import StringCharacter, PatchState, GadgetBase
from .direct_byte_assignment import DirectByteAssignment
from .xor64_assignment import Xor64Assignment
from .xor32_assignment import Xor32Assignment
from .misaligned_jump import MisalignedJump
from .roundabout import Roundabout


## List of assembly gadgets that can be used to assign one or more characters of a protected string.
available_assignment_gadgets = [
    DirectByteAssignment,
    Xor64Assignment,
    Xor32Assignment,
]

## List of assembly gadgets that just consume bytes and obfuscate things.
available_junk_gadgets = [
    MisalignedJump,
    Roundabout
]





    





