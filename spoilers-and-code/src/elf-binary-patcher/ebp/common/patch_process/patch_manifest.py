
# python imports
from typing import TypeVar
from pathlib import Path
from json import load, dump
from datetime import datetime
from copy import copy

## The @ref PatchManifest object self type.
PatchManifestType = TypeVar('PatchManifestType', bound='PatchManifest')

       
# project imports
from .data_dependency import DataDependencyList

## Patch Manifest Object
#  This object contains information about the patch process. 
#  This used to record useful debugging information and data that might 
#  be useful across patch operations (such as the location of data that is 
#  sensitive and shouldn't be changed, or junk bytes that can be altered 
#  at will)
class PatchManifest(object):
    
    ## Determines the expected manifest location for the given ELF file.
    #  The manifest accompanies the ELF during the build process, this 
    #  method can be used to determine where it should be found.
    #  @param cls the type of class that is invoking this method.
    #  @param path the file path to the ELF we want the manifest for.
    #  @returns the expected path of the manifest file.
    @classmethod
    def elfPathToManifestPath(cls, path:Path) -> Path:
        directory = path.parent
        manifest_name = f"{path.name}.ebp.manifest"
        return directory / manifest_name


    ## Gets a manifest for the given ELF file (if one doesn't exist it will be created in memory).
    #  @param cls the type of class that is invoking this method.
    #  @param path the path of the ELF to get a manifest for.
    #  @returns an instance of the ELF manifest class.
    @classmethod
    def forElf(cls, path:str) -> PatchManifestType:

        elf_path = Path(path)
        manifest_path = cls.elfPathToManifestPath(elf_path)
        manifest_instance = cls()

        if manifest_path.exists():
            with manifest_path.open('r') as fh:
                manifest_json = load(fh)
            manifest_instance.apply_json(manifest_json)

        return manifest_instance


    ## Saves the ELF manifest file.
    #  @param self the instance of the object that is invoking this object.
    #  @param elf_path the path that the ELF file is being serialised to.
    def save(self, elf_path:str) -> None:
        
        elf_path = Path(elf_path)
        manifest_path = self.elfPathToManifestPath(elf_path)

        self.last_saved = datetime.now()
        self.last_saved_path = elf_path

        manifest_json = self.to_json()

        with manifest_path.open('w') as fh:
            dump(manifest_json, fh)


    ## Creates a new instance of this object.
    #  @param self the instance of the object that is invoking this object.
    def __init__(self) -> PatchManifestType:

        self.last_saved = None                          # when the elf file was last written.
        self.last_saved_path = None                     # where the elf file was written to.         
        self.data_dependencies = DataDependencyList()   # a list of offsets that are being used as data and should not be altered.
        self.junk_offsets = []                          # a lsit of offsets that are junk and can be arbitrarily altered.


    ## Creates a copy of this elf manifest
    #  This is mostly used for snapshotting before a tentative path. The copy must be entirely stand alone for this reason.
    #  @param self the instance of the object that is invoking this object.
    #  @returns a new, duplicate instance of this object.
    def copy(self) -> PatchManifestType:
        manifest_copy = copy(self)
        manifest_copy.data_dependencies = copy(self.data_dependencies)
        manifest_copy.junk_offsets = copy(self.junk_offsets)
        return manifest_copy
    

    ## Converts the object to JSON notation for serialisation.
    #  @param self the instance of the object that is invoking this method.
    #  @returns this object, expressed as a dict object that can be serialised.
    def to_json(self) -> dict:
        return {
            'last-saved': self.last_saved.strftime("%Y-%m-%d %H:%M:%S"),
            'last-saved-path': str(self.last_saved_path),
            'data-dependencies': self.data_dependencies.to_json(),
            'junk-offsets': self.junk_offsets,
        }

    ## Applies data loaded in JSON notorisation to this object.
    #  @param self the instance of the object that is invoking this method.
    #  @param json the JSON data to apply to the object.
    def apply_json(self, json:dict) -> None:
        
        data_depdendencies = json.get('data-dependencies', [])
        last_saved_path = json.get('last-saved-path', None)
        last_saved_date = json.get('last-saved', None)

        self.junk_offsets = json.get('junk-offsets', [])
        self.data_dependencies = DataDependencyList.fromJson(data_depdendencies)
        self.last_saved_path = None if not last_saved_path else Path(last_saved_path)
        self.last_saved = None if not last_saved_date else datetime.strptime(
            last_saved_date, "%Y-%m-%d %H:%M:%S"
        )