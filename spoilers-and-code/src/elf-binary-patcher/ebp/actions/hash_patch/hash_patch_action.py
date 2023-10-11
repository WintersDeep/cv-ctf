
# python3 imports
from argparse import ArgumentParser
from typing import List, Type, Any
from pathlib import Path

# third-party imports
from pwnlib.elf import ELF

# project imports
from ebp.actions.base import InOutPatchActionBase, VolatileLocation, VolatileLocationList
from .hash_patch_sections import HashPatchSections

## "Hash Patch" action.
#  Looks for `.hash-patch.` sections which should mark locations that the ELF file has code related to the binaries integrity.
#  The tooling has various jobs to perform around this from injecting valid hashes - to making sure "volitile" VMA is jumped 
#  over (for example; its kind of hard to include the integrity hash as part of the intgrity hash itself).
class HashPatchAction(InOutPatchActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "hash-patch"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "finalises the integrity checking mechanisms of the binary."


    ## Gets a list of all the offsets that are inherently "unpredictable" and should be skipped by the integrity check.
    #  @param self the instance of the object that is invoking this method.
    #  @param sections the sections of the binary that has been identified as relating to the binaries integrity.
    #  @returns a list of all known QWORD offsets that may impact the value of the integrity hash.
    def find_all_unsigned_qwords(self, sections:List) -> List[int]:
        unsigned_qwords = set()
        unsigned_qwords.update( *(d.unverified_offsets() for d in sections) )
        return sorted(unsigned_qwords)


    ## Patches all the non-volatile parts of the binary (those types that can be incleded in the integrity hash).
    #  @param self the instance of the object that is invoking this method.
    #  @param section_list a list of all the components of the integrity system that we are aware of.
    #  @returns the state of any types that performed non-volatile patching.
    def patch_non_volatile_components(self, section_list:HashPatchSections) -> dict[Type, Any]:

        non_volatile_states = {}

        self.log.info(f"Initialising non-volatile aspects of integrity...")
        for section_type in set( s.__class__ for s in section_list ):
            type_state = section_type.configure_non_volatile(section_list)
            if type_state: non_volatile_states[section_type] = type_state

        self.log.info(f"Patching non-volatile aspects of integrity system for {len(non_volatile_states)} types...")
        for section_type, state in non_volatile_states.items():
            section_type.patch_non_volatile(state)

        return non_volatile_states

    ## Patches all the volatile parts of the binary (those types that cannot be incleded in the integrity hash).
    #  @param self the instance of the object that is invoking this method.
    #  @param section_list a list of all the components of the integrity system that we are aware of.
    #  @returns the state of any types that performed volatile patching.
    def patch_volatile_components(self, section_list:HashPatchSections, non_volatile_states) -> dict[Type, Any]:

        volatile_states = {}

        self.log.info(f"Initialising volatile aspects of integrity...")
        for section_type in set( s.__class__ for s in section_list ):
            type_non_volatile_state = non_volatile_states.get(section_type, None)
            type_state = section_type.configure_volatile(section_list, type_non_volatile_state)
            if type_state: volatile_states[section_type] = type_state

        self.log.info(f"Patching volatile aspects of integrity system for {len(volatile_states)} types...")
        for section_type, state in volatile_states.items():
            section_type.patch_volatile(state)

        return volatile_states

    ## Returns a list of volatile locations this action is aware of.
    #  This is needed as some actions reflectively pull data from the binary and need to pick locations that
    #  are not going to be subject to change.
    #  @param cls the type of class invoking this method.
    #  @param elf the elf to locate volatile regions in.
    #  @returns a list of volatile regions in the binary.
    @classmethod
    def volatile_locations(cls, elf:ELF) -> VolatileLocationList:
        
        volatile_locations_list = VolatileLocationList()
        
        for section in HashPatchSections.fromElf(elf):
            volatile_locations_list.extend( VolatileLocation(*offsets) for offsets in section.unstable_offsets())
            
        return volatile_locations_list


    ## Invokes this action on an ELF file.
    #  This action will take protected strings from the binary and inject code to build the required strings.
    #  @param elf the ELF file this action should operate on.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = self.__class__.ExitSuccess

        self.log.info(f"Starting to patch integrity mechanisms in '{self.arguments.elf.path}'.")
        
        try:
            section_list = HashPatchSections.fromElf(self.arguments.elf)
            
            non_volatile_state = self.patch_non_volatile_components(section_list)
            self.patch_volatile_components(section_list, non_volatile_state)

            self.log.info(f"Finished patching integrity mechanisms as '{self.arguments.out_file}'.")
        
            self.arguments.elf.save(self.arguments.out_file)

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = self.__class__.ExitRuntimeError
        
        return exit_code
