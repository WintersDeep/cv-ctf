# python imports
from random import randint
from typing import List, TypeVar, Optional, Any
from types import TracebackType

# third-party imports
from pwnlib.elf import ELF as pwnlib_elf
from elftools.elf.sections import Section

# project imports
from ebp.x64asm import ScopedJunkHook
from .patch_manifest import PatchManifest
from .data_dependency import DataDepdendency


## Self type for the @ref Elf type.
ElfType = TypeVar('ElfType', bound="Elf")

## Self type for the @ref TentativePatch type.
TentativePatchType = TypeVar('TentativePatchType', bound='TentativePatch')

## Because sometimes we don't know where we are going.
#  Allows changes to the patch manifest to be "rolled back". Can extend this to the ELF bytes if we really need to.
class TentativePatch(object):


    ## Creates a new instance of the tentative patch object.
    #  @param self the instance of the object that is invoking this method.
    #  @param elf the ELF file we might need to undo changes in.
    def __init__(self, elf:ElfType) -> TentativePatchType:
        self.elf = elf
        self.manifest = elf.manifest_snapshot()
        self.changes_confirmed = False


    ## Confirms the patch and accepts changes.
    #  If this is not called then the changes will be rolled back when leaving scope.
    #  @param self the instance of the object that is invoking this method.
    def confirm(self) -> None:
        self.changes_confirmed = True


    ## Invoked when we enter `with` scope.
    #  @param self the instance of the object that is invoking this method.
    def __enter__(self) -> None:
        return self

    ## Invoked when we leave `with` scope.
    #  @param self the instance of the object that is invoking this method.
    #  @param exc_type the type of exception that caused us to exit `with` scope if any, else None.
    #  @param exc_value the exception that caused us to exit `with` scope if any, else None.
    #  @param traceback the exception traceback that caused us to exit `with` scope if any, else None.
    def __exit__(self, exc_type:Optional[type], exc_value:Optional[Exception], traceback:Optional[TracebackType]):
        if not self.changes_confirmed:
            self.elf.restore_manifest(self.manifest)



## Elf extension class.
#  Provides some extensions to the library ELF class.
class Elf(pwnlib_elf):


    ## Creates a new instance of this object.
    #  @note adds a patch manifest member to all loaded ELF files.
    #  @param self the instance of the object that is invoking this method.
    #  @param path the path of the ELF binary we are loading.
    #  @param args positional arguments provided to constructor (see pwnlib documentation).
    #  @param kwargs keyword arguments provided to constructor (see pwnlib documentation).
    def __init__(self, path:str, *args:list, **kwargs:dict) -> ElfType:
        super().__init__(path, *args, **kwargs)
        self.patch_manifest = PatchManifest.forElf(path)


    ## Starts a tentative patch of the ELF.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a context manager to manage changes to the binary.
    def start_tentative_patch(self) -> TentativePatch:
        return TentativePatch(self)


    ## Writes data to the elf file.
    #  @note overriden to allow checking of data dependencies and avoid clobbering.
    #  @param self the instance of the object that is invoking this method.
    #  @param address the address that writing starts at.
    #  @param bytes_ the bytes to write to the address.
    def write(self, address:int, bytes_:bytes) -> None:

        bytes_length = len(bytes_)

        # check for data dependency collisions...
        if self.patch_manifest.data_dependencies.has_dependency(address, bytes_length):
            data_depdendencies = self.patch_manifest.data_dependencies.collisions(address, bytes_length)
            addresses = "\n".join( f"- 0x{d.start_address:08x} -> 0x{d.finish_address:08x} ({d.length} bytes): {d.message}" for d in data_depdendencies )
            raise RuntimeError(f"DANGER: attempted to write to 0x{address:08x} -> 0x{address+bytes_length:08x} ({bytes_length} bytes), but this clobbers registered data dependencies:\n" + addresses)
        
        super().write(address, bytes_)


    ## Registers any junk bytes that are creating within the given scope.
    #  @param self the instance of the object that is invoking this method.
    #  #@returns a context manager to scope junk hooking.
    def register_junk_in_context(self) -> ScopedJunkHook:
        return ScopedJunkHook(self.register_junk)


    ## Registers a given offset within the binary as holding a junk value that can be arbitrarily changed.
    #  @param self the instance of the object that is invoking this method.
    #  @param address the address of the byte to note as being junk.
    def register_junk(self, address:int) -> None:
        assert not self.patch_manifest.data_dependencies.has_dependency(address, 1)
        return self.patch_manifest.junk_offsets.append(address)


    ## Gets a list of available junk offsets.
    #  @param self the instance of the object that is invoking this method.
    #  @return list of offsets that contain junk values.
    def junk_available(self) -> List[int]:
        return self.patch_manifest.junk_offsets

    ## Assigns the requires value to a junk offset and returns that address.
    #  @param self the instance of the object that is invoking this method.
    #  @param value the value that we want to assign.
    #  @param message the reason we need that value (for a data dependency message)
    #  @returns the address of the junk byte that was assigned.
    def assign_junk(self, value, message) -> int:

        # convert the value to bytes if needed.
        if isinstance(value, int):
            assert value & 0xff == value, "too much data for junk byte"
            value = bytes([value])

        # make sure the value fits in a byte
        assert len(value) == 1, "too much data for junk byte"

        # assign a junk value
        index = randint(0, len(self.patch_manifest.junk_offsets) - 1)
        address = self.patch_manifest.junk_offsets.pop(index)
        self.write(address, value)
        
        # notorise the new dependency
        self.record_data_dependency(address, 1, message)

        # return address
        return address


    ## Saves the Elf file.
    #  @note overwritten to also save manifest file on save() call.
    #  @param self the instance of the object that is invoking this method.
    #  @param path the path to save the binay at, if ommited uses load path.
    #  @returns check pwnlib documentation.
    def save(self, path:str=None) -> Any:
        if path is None:
            path = self.path
        self.patch_manifest.save(path)
        return super().save(path)


    ## Takes a snapshot of the manifest.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a duplicate copy of the current patch manifest file.
    def manifest_snapshot(self) -> PatchManifest:
        return self.patch_manifest.copy()

    ## Sets the current patch manifest.
    #  Used to restore a previous manifest if patching fails.
    #  @param self the instance of the object that is invoking this method.
    #  @param manifest the manifest to restore.
    def restore_manifest(self, manifest:PatchManifest) -> None:
        self.patch_manifest = manifest


    ## Records a new data depdendency in this elf.
    #  @param self the instance of the object that is invoking this method.
    #  @param virtual_memory_address the address of the data depdendency.
    #  @param length the size of the dependency.
    #  @param message the reason we are not dependent on this address range.
    def record_data_dependency(self, virtual_memory_address, length, message=None) -> None:
        for address in range(virtual_memory_address, virtual_memory_address + length):
            if address in self.patch_manifest.junk_offsets:
                index = self.patch_manifest.junk_offsets.index(address)
                del self.patch_manifest.junk_offsets[index]
        
        dependency = DataDepdendency(virtual_memory_address, length, message)
        self.patch_manifest.data_dependencies.append(dependency)


    ## Determines which section the given address resides in.
    #  @param self the instance of the object that is invoking this method.
    #  @param address the address to get the containing section for.
    #  @returns the section this descriptor is targetting.
    def get_section_containing(self, address:int) -> Section:
        sections = self.get_all_sections_containing(address)
        number_of_sections = len(sections)
        
        # NOTE: neither of these cases should occur, but we are modifying the binary at a pretty low level and I can be pretty dumb so...
        if number_of_sections == 0:
            raise RuntimeError(f"Unable to find section for 0x{address:016x} - this address does not seem to fall into any sections?")
        elif number_of_sections > 1:
            raise RuntimeError(f"Unable to find section for 0x{address:016x} - this address appears in {number_of_sections} overlapping(?) sections.")

        return sections[0]


    ## Determines the sections that a given memory address can appear in.
    #  NOTE: this returns a list - if the ELF is healthy and we've not goofed there should only ever be 0 or 1 items in this list.
    #  @param self the instance of the object that is invoking this method.
    #  @param address the address tha we wish to try to find the owning section of.
    #  @returns a list of sections that contain the given virtual memory address.
    def get_all_sections_containing(self, address:int) -> List[Section]:
        sections = []
        for section in self.sections:
            section_start = section.header.sh_addr
            section_ends = section_start + section.header.sh_size
            if address >= section_start and address <= section_ends:
                sections.append(section)
        return sections
