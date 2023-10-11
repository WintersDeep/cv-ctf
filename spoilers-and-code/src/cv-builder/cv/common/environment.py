# python imports
from os import environ
from typing import TypeVar
from pathlib import Path

## Self type for the @ref Environment object class.
EnvironmentType = TypeVar('EnvironmentType', bound='Environment')


## Shortcut for building environments for subprocesses to work in.
class Environment(dict):

    ## Creates an environment variable that expresses an unsigned long in GCC.
    #  @param cls the type of class that is invoking this method.
    #  @param unsigned_long the value to encode.
    #  @returns string that can be set as an environment for the given value.
    @classmethod
    def GccUnsignedLong(cls, unsigned_long:int) -> str:
        return f"{unsigned_long}UL"

    ## Creates an environment variable that expresses a string in GCC.
    #  @param cls the type of class that is invoking this method.
    #  @param string the value to encode.
    #  @returns string that can be set as an environment for the given value.
    @classmethod
    def GccString(cls, string:str) -> str:
        return f'"{string}"'

    ## Creates an environment variable that expresses a directory path.
    #  @param cls the type of class that is invoking this method.
    #  @param path the directory path to output.
    #  @param create a boolean indicating if the path should be created (if it doesn't exist)
    #  @returns string that can be set as an environment for the given value.
    @classmethod
    def Directory(cls, path:str|Path, create:bool=True) -> str:
        directory_path = Path(path)
        directory_path.mkdir(parents=True, exist_ok=True)
        return str(directory_path)
    
    ## Creates an environment variable that expresses a directory path which contains the given file.
    #  @param cls the type of class that is invoking this method.
    #  @param path the file path to extract a directory from.
    #  @param create a boolean indicating if the path should be created (if it doesn't exist)
    #  @returns string that can be set as an environment for the given value.
    @classmethod
    def FileDirectory(cls, path:str|Path, create:bool=True) -> str:
        file_path = Path(path)
        return cls.Directory(file_path.parent, create)
    
    ## Creates an environment variable that expresses a file name.
    #  @param cls the type of class that is invoking this method.
    #  @param path the file path to extract the name from.
    #  @returns string that can be set as an environment for the given value.
    @classmethod
    def FileName(cls, path:str|Path) -> str:
        file_path = Path(path)
        return file_path.name  

    ## Creates a new instance of this class.
    #  @param self the type of object that is invoking this method.
    #  @param initial_variable initial environment variables to put on top of the existing environment
    def __init__(self, **initial_variables:dict) -> EnvironmentType:
        super().__init__()
        self.update(environ)
        self.update(initial_variables)


## Environment shortcut - because I am lazy when it comes to assigning values into an environment.
E = Environment
    