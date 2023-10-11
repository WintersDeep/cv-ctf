# python imports
from tempfile import NamedTemporaryFile
from typing import TypeVar, Optional
from types import TracebackType
from pathlib import Path
from re import compile as regex_compile

## Self type for the @ref ModifiedContent class
ModifiedContentType = TypeVar('ModifiedContentType', bound='ModifiedContent')

## Context manager to create life-time limited copies of files with altered content.
class ModifiedContent(object):

    ## Creates a new instance of this object.
    #  @param self the instance of the object that is invoking this method.
    #  @param file the file to modify the content of.
    #  @param replacement_map map of regular expressions to replacements to make in the original file.
    #  @param binary whether to open the file in binary or text mode (defaults to text)
    def __init__(self, file:Path, replacement_map:dict, binary:bool=False) -> ModifiedContentType:
        self.original_file_path = Path(file)
        self.replacement_map = replacement_map
        self.binary_mode = binary
        self.temp_file = None

    
    ## Invoked when we enter `with` scope.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the path to the altered file.
    def __enter__(self) -> Path:
        
        mode = "b" if self.binary_mode else ""

        with self.original_file_path.open(f"r{mode}") as original_fh:
            original_content = original_fh.read()

        for regex_pattern, const_replacement in self.replacement_map.items():
            regex = regex_compile(regex_pattern) if isinstance(regex_pattern, str) else regex_pattern
            original_content = regex.sub(const_replacement, original_content)

        temp_file = NamedTemporaryFile(f"w{mode}", delete=False)
        temp_file.write(original_content)
        temp_file.close()

        self.temp_file = Path(temp_file.name)
        return self.temp_file
    

    ## Invoked when we leave `with` scope.
    #  @param self the instance of the object that is invoking this method.
    #  @param exc_type the type of exception that caused us to exit `with` scope if any, else None.
    #  @param exc_value the exception that caused us to exit `with` scope if any, else None.
    #  @param traceback the exception traceback that caused us to exit `with` scope if any, else None.
    def __exit__(self, exc_type:Optional[type], exc_value:Optional[Exception], traceback:Optional[TracebackType]) -> None:
        self.temp_file.unlink()