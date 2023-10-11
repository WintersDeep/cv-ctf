# python imports
from pathlib import Path
from tempfile import TemporaryDirectory

# third-party imports
from pyminizip import compress_multiple

# project imports
from cv.build_steps.base import BuildStep


## Creates an encrypted ZIP file.
class MakeEncryptedZip(BuildStep):

    ## Creates a new instance of this build step.
    #  @param self the instance of the object that is invoking this method.
    #  @param zip_location the location of the ZIP file.
    #  @param zip_password the password to use for the ZIP file.
    #  @param files a map of files to add to the ZIP with keys representing the path in the ZIP and values their uncompressed source.
    def __init__(self, zip_location:Path, zip_password:str, files:dict[str, Path], zip_compression:int = 9):
        self.zip_location = zip_location
        self.zip_password = zip_password
        self.zip_compression = zip_compression
        self.file_map = files


    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    def __call__(self) -> bool:

        missing_files = [ str(file) for file in self.file_map.values() if not file.exists() ]
                
        if any(missing_files): 
            missing_file_list = ",".join(missing_files)
            raise RuntimeError(f"Can't build encrypted ZIP because the following files are missing; {missing_file_list}")
                
        source_files = []
        zip_files = []

        with TemporaryDirectory() as zip_directory:

            zip_root = Path(zip_directory)

            for destination, source in self.file_map.items():
                
                file_path = Path(destination)
                
                directory_name = file_path.parent
                
                temp_path = zip_root / file_path 
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path.symlink_to(source)

                source_files.append(str(temp_path))

                output_directory = str(directory_name)
                if output_directory == "." or output_directory.startswith("./"):
                    output_directory = output_directory[1:]

                zip_files.append(output_directory)
                

            if self.zip_location.exists(): self.zip_location.unlink()

            compress_multiple(source_files, zip_files, str(self.zip_location), self.zip_password, self.zip_compression)

            return self.zip_location.exists()


