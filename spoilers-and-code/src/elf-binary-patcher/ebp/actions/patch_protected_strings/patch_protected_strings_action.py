# python imports
from argparse import ArgumentParser
from random import shuffle
from typing import List
from pathlib import Path

# third-party imports
from pwnlib.elf import ELF

# project imports
from ebp.actions.base import InOutPatchActionBase, VolatileLocation, VolatileLocationList
from .protected_string import ProtectedString
from .gadgets import available_assignment_gadgets, available_junk_gadgets, StringCharacter
from .gadgets.base import GadgetList


## Protected string action.
#  Looks for `.protected-string.#` sections which should mark locations that the ELF file has reserved space to build a string. 
#  Its this actions job to locate fill the reserved space with assembly instructions to build the requested string.
class PatchProtectedStringsAction(InOutPatchActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "protect-strings"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "implements code to unpack strings in locations identified by .protected-strings.# sections."

    ## Maximum number of times we will try to patch the string before giving up.
    #  @remarks usual failure mode is size related; the number of opcodes generated is variable and its possible that we generate 
    #     a gadget chain that doesn't fit in the reservation space (or if we always compile with space we likely being too generous
    #     the the bytes allocated).
    MaxPatchTries = 10


    ## Generates a list of assignment gadgets to build the specified @p protected_string
    #  @param self the instance of the object that is invoking this method.
    #  @param protected_string the protected string that we wish to build in memory.
    #  @returns a list of gadgets that could build the target string.
    def select_assignment_gadets(self, protected_string:ProtectedString) -> GadgetList:
        
        character_manifest = StringCharacter.Manifest(protected_string.expected_string + b"\0")
        assignment_gadgets = available_assignment_gadgets.copy()
        gadget_list = GadgetList()

        while character_manifest:

            shuffle(assignment_gadgets)

            for gadget in assignment_gadgets:
                
                gadget_instance = gadget.offer(character_manifest)
                
                if gadget_instance:
                    self.log.debug(f"Selected {gadget_instance.name} gadget.")
                    gadget_list.append(gadget_instance)
                    break
            
            else:
                # no gadget accepted any of the remaining characters - this shouldn't be possible assuming we have a gadget that will accept single characters.
                msg = "Offered remaining characters to all available assignment gadgets but none of them were willing to claim any - this should never happen."
                raise RuntimeError(msg)

        self.log.debug(f"Selected {len(gadget_list)} assignment gadgets to build {len(protected_string.expected_string) + 1} byte string.")

        return gadget_list


    ## Injects junk gadgets into the given @p gadget_list that will consume up to @p available_space bytes.
    #  Junk gadgets may modify the gadget list in a variety of ways, but should never add more than @p available_space bytes to the generated opcode.
    #  @param self the instance of the object that is invoking this method.
    #  @param available_space the amount of space available for junk gadgets.
    #  @param gadget_list the list of gadgets to inject junk into.
    #  @returns the amount of space that was not claimed by junk gadgets.
    def inject_junk_gadgets(self, available_space:int, gadget_list:GadgetList) -> int:
        
        junk_gadgets = available_junk_gadgets.copy()

        while available_space > 0:

            shuffle(junk_gadgets)

            for gadget in junk_gadgets:

                junk_gadget = gadget.apply(available_space, gadget_list)

                if junk_gadget:
                    self.log.debug(f"Injected; {junk_gadget.name}.")
                    available_space -= junk_gadget.size
                    break
            else:
                self.log.debug(f"{available_space} bytes unallocatable to junk and remain as NOP.")
                break

        return available_space
                    


    ## Patches the given @p protected_string in the ELF binary.
    #  @param self the instance of the object that is invoking this method.
    #  @param protected_string the string that we want to build in software.
    #  @returns a list of opcodes that will build the protected string in memory.
    def genereate_protected_string_patch(self, protected_string:ProtectedString) -> List[int]:

        for attempt_index in range(1, self.MaxPatchTries + 1):
            
            with protected_string.elf.start_tentative_patch() as tentative_patch:
            
                # pick some assignment gadgets to build the string
                self.log.debug(f"Attempting to generate gadet list (attempt #{attempt_index}/{self.MaxPatchTries}).")
                gadget_list = self.select_assignment_gadets(protected_string)
                
                # part-compile the gadget to determine length of generated opcodes...
                # (the exact opcodes will change on each compile - but assuming the same starting state the size should be consistent).
                assembly_list = gadget_list.compile_flat(protected_string.elf, protected_string.virtual_memory_address)
                opcode_size = assembly_list.opcodes_length()
                delta_bytes = protected_string.reservation_size - opcode_size
                capacity_percentage = ((opcode_size / protected_string.reservation_size)) * 100
                self.log.debug(f"Generated solution size guidance; ({opcode_size}/{protected_string.reservation_size} bytes, {delta_bytes} bytes free, {capacity_percentage:.0f}% capacity).")

                if delta_bytes >= 0:
                    tentative_patch.confirm()
                    break

            self.log.debug("Gadget chain too large; discarding...")

        else: # we failed to build a gadget chain that fits in the reserved space.
            error_message = f"Giving up on generating a gadet chain for '{protected_string.section.name}' that fits inside the {protected_string.reservation_size} byte reservation space after {self.MaxPatchTries} attempts."
            self.log.error(error_message)
            raise RuntimeError(error_message)
            

        # fill any unused space with junk gadgets.
        unallocated_reservation = protected_string.reservation_size - opcode_size
        self.inject_junk_gadgets(unallocated_reservation, gadget_list)

        # emit patched opcode
        assembly_list = gadget_list.compile_flat(protected_string.elf, protected_string.virtual_memory_address)
        
        with protected_string.elf.register_junk_in_context() as _:
            return assembly_list.opcodes(protected_string.virtual_memory_address)


    ## Returns a list of locations that are going to be re-written/changed by this action.
    #  This is needed as some actions reflectively pull data from the binary and need to pick locations that
    #  are not going to be subject to change.
    #  @param cls the type of class invoking this method.
    #  @param elf the elf to locate volatile regions in.
    #  @returns a list of volatile regions in the binary.
    @classmethod
    def volatile_locations(cls, elf:ELF) -> VolatileLocationList:
        
        protected_string_volatiles = []
        protected_string_list = list( ProtectedString.fromElf(elf) )
        
        for protected_string in protected_string_list:

            if protected_string.virtual_memory_found():

                start_volatile = protected_string.virtual_memory_address

                protected_string_volatiles.append(VolatileLocation(
                    start_volatile, protected_string.reservation_size
                ))

        return protected_string_volatiles
        


    ## Invokes this action on an ELF file.
    #  This action will take protected strings from the binary and inject code to build the required strings.
    #  @param elf the ELF file this action should operate on.
    #  @returns patch process exit code.
    def __call__(self) -> None:

        exit_code = self.__class__.ExitSuccess

        try:
            self.log.info(f"starting to patch protecting strings in '{self.arguments.elf.path}'.")
            
            protected_string_list = list( ProtectedString.fromElf(self.arguments.elf) )
            
            for index, protected_string in enumerate( protected_string_list ):

                if protected_string.virtual_memory_found():
                
                    self.log.info(f"Patching protected string #{index + 1}/{len(protected_string_list)} - {protected_string.section.name} (~0x{protected_string.virtual_memory_address:016x}).")

                    patch_opcodes = self.genereate_protected_string_patch(protected_string)
                    
                    assert len(patch_opcodes) <= protected_string.reservation_size, \
                        f"invalid patch size; {len(patch_opcodes)} byte geneated > {protected_string.reservation_size} bytes available"

                    self.arguments.elf.write(protected_string.virtual_memory_address, patch_opcodes)
                    
                    number_of_characters = len(protected_string.expected_string)
                    number_of_opcodes = len(patch_opcodes)
                    bytes_per_char = number_of_opcodes / number_of_characters
                    self.log.info(f"Finished patching protected string #{index + 1}/{len(protected_string_list)} - {number_of_opcodes} bytes ASM, {number_of_characters} chars, ~{bytes_per_char:.2f}bytes/char, 0x{protected_string.virtual_memory_address:016x}.")

                else:
                    self.log.warn(f"Unable to find reservation for protected string #{index + 1}/{len(protected_string_list)} - {protected_string.section.name} (~0x{protected_string.virtual_memory_address:016x}).")

            self.arguments.elf.save(self.arguments.out_file)
        
        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = self.__class__.ExitRuntimeError

        return exit_code