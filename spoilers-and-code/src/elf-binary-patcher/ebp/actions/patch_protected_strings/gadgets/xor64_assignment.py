# project imports
from .xor_assignment_base import XorAssignmentBase
from ebp.x64asm import (
    MOV_RAX_QWORDPTR_ripoff,
    MOV_QWORDPTR_RBX_RAX
)


## This gadget will look for 8 consecutive characters and use an 64bit XOR to assign them all at once.
#  The values used to XOR will be sourced from memory rather than fixed values where possible.
class Xor64Assignment(XorAssignmentBase):

    ## The size of the assignment in bytes.
    Size = 8

    ## The ASM instruction used to pull the appropriate amount of bytes into A from a RIP offset.
    MovInCls = MOV_RAX_QWORDPTR_ripoff

    ## The ASM instruction used to push the appropriate amount of bytes from A into the memory pointed to by B.
    MovOutCls = MOV_QWORDPTR_RBX_RAX