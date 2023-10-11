# project imports
from .xor_assignment_base import XorAssignmentBase
from ebp.x64asm import (
    MOV_EAX_DWORDPTR_ripoff,
    MOV_DWORDPTR_RBX_EAX
)


## This gadget will look for 4 consecutive characters and use an 32bit XOR to assign them all at once.
#  The values used to XOR will be sourced from memory rather than fixed values where possible.
class Xor32Assignment(XorAssignmentBase):
    
    ## The size of the assignment in bytes.
    Size = 4

    ## The ASM instruction used to pull the appropriate amount of bytes into A from a RIP offset.
    MovInCls = MOV_EAX_DWORDPTR_ripoff

    ## The ASM instruction used to push the appropriate amount of bytes from A into the memory pointed to by B.
    MovOutCls = MOV_DWORDPTR_RBX_EAX