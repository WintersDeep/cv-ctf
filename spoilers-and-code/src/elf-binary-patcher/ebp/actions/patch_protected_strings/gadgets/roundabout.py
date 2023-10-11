# python3 imports
from typing import TypeVar, List
from random import randint

# project imports
from .base import GadgetBase, JunkGadget, PatchState, GadgetList
from ebp.x64asm import InstructionList, JMP_ripoff, JunkByte


## The @ref Roundabout `Self` type
SelfType = TypeVar('SelfType', bound='Roundabout')


## Junk gadget that jumps around another gadget.
#  A simple extenion of the misaligned jump gadget. This junk gadget will "wrap" an existing gadget.
#  It will create a jump/junk to the end of the wrapped gadget, another to jump back to the gadget, and 
#  one to exit the original gadget. The junk bytes are designed to mess with the compiler and make it 
#  harder to determine where execution flow goes without executing it (shown below in ASCII art):
#
#  RIP
#   |  :         VVVVVVVV         :
#   |  :                          :
#   |=============================== \
#   |  | jmp X                    |
#   |  +--------------------------+
#   |  :       JUNK BYTE(S)       :
#   |  +--------------------------+
#   Y  :                          :
#   |  :   >WRAPPED GADGET HERE   :
#   |  :                          :
#   |  +--------------------------+
#   |  | jmp Z                    |
#   |  +--------------------------+
#   |  :       JUNK BYTE(S)       :
#   |  +--------------------------+
#   X  | jmp Y                    |
#   |  +--------------------------+
#   |  :       JUNK BYTE(S)       :
#   |=============================== /
#   Z  :                          :
#   |  :         VVVVVVVV         :
#   |
class Roundabout(JunkGadget):


    ## Gets the size of this gadget
    #  @remarks note that this isn't the same as the compiled size - its the size the gadget occupies.
    #    the total size of this gadget would also need to include the opcodes generated from the 
    #    wrapped gadget - in the context this is used though this is already accounted for.
    size = (JMP_ripoff.opcodes_length() * 3) + \
           (JunkByte.opcodes_length() * 3)


    ## Instanciates a new @ref Roundabout object.
    #  @param self the instance of the object that is invoking this method.
    #  @param wrapped_gadget the gadget that we are wrapping with the roundabout.
    def __init__(self, wrapped_gadget:GadgetBase) -> SelfType:
        self.wrapped_gadget = wrapped_gadget


    ## Applies the junk gadget to the given gadget list.
    #  @param cls the type of class executing this method.
    #  @param space_available the number of bytes available for junk gadgets.
    #  @param gadget_list the current gadget list - this will by modified if a gadget is applied.
    #  @returns the instance of the gadget that was created and inserted into @p gadget_list (if one was created), else None.
    @classmethod
    def apply(cls, space_available, gadget_list:GadgetList) -> GadgetBase:
        
        gadget_instance = None

        if space_available >= cls.size:
            gadget_index = randint(0, len(gadget_list) - 1)
            wrapped_gadget = gadget_list[gadget_index]
            gadget_instance = cls(wrapped_gadget)
            gadget_list[gadget_index] = gadget_instance

        return gadget_instance


    ## Determines the name of this gadget.
    #  @param self the instance of the object that is invoking this method.
    #  @returns string that describes this object behaviour.
    @property
    def name(self) -> str:
        return f"round-about junk gadget containing {self.wrapped_gadget.name}"



    ## Compiles the gadet into assembly instructions.
    #  @param self the instance of the object invoking this method.
    #  @param state the state of the patch process.
    #  @returns a list of instructions to achieve the outcome.
    def compile(self, state:PatchState) -> InstructionList:

        # compile inner widget
        wrapped_gadget_instructions = self.wrapped_gadget.compile(state)

        # calculate jump distances
        jump_back_distance = (JunkByte.opcodes_length() * 1) + \
                             (JMP_ripoff.opcodes_length() * 2) + \
                             wrapped_gadget_instructions.opcodes_length()
        
        jump_out_distance = (JunkByte.opcodes_length() * 2) + \
                             (JMP_ripoff.opcodes_length() * 1)

        jump_over_distance = jump_out_distance + wrapped_gadget_instructions.opcodes_length()

        # build widget.
        instructions =  InstructionList()
        instructions.append(JMP_ripoff(jump_over_distance, is_relative=True))
        instructions.append(JunkByte( randint(0x00, 0xff) ))
        instructions.extend(wrapped_gadget_instructions)
        instructions.append(JMP_ripoff(jump_out_distance, is_relative=True))
        instructions.append(JunkByte( randint(0x00, 0xff) ))
        instructions.append(JMP_ripoff(-jump_back_distance, is_relative=True))
        instructions.append(JunkByte( randint(0x00, 0xff) ))
        return instructions

        
        
