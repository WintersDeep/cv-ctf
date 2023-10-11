# python3 imports
from typing import TypeVar
from pathlib import Path

# third-party imports
from fitz import Document


## Self type for the @ref PdfDocument object type.
SelfType = TypeVar('SelfType', bound="PdfDocument")


## A Pdf document
#  Extension to the native fitz type to hang extensions off.
class PdfDocument(Document):

    ## Creates a new instance of the PDF document type.
    #  @param self the instance of the object that is invoking this method.
    #  @param file_path the file path to load data from.
    #  @param args positional arguments applied to the underlying PDF type - see fitz documentation.
    #  @param kwargs keyword arguments applied to the underlying PDF type - see fitz documentation.
    def __init__(self, file_path:str, *args:list, **kwargs:dict) -> SelfType:
        super().__init__(file_path, *args, **kwargs)
        self.path = Path(file_path) if file_path else None