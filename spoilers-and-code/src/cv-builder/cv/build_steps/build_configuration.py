# python3 imports
from typing import Any
from pathlib import Path
from json import load
from datetime import datetime

# project imports
from cv.common import ModifiedContent


## Build configuration object.
#  Used to control how the CV is built in the `build` one-step action.
#  @tbd lots of cleanup needed here - everything expects "good values", no way to generate an empty config.
#    its a good job this is internal and only used by me.
class BuildConfiguration(dict):

    ## Create a new instance of this object.
    #  @param self the instance of the object that is invoking this method.
    #  @param path the path of the configuration file to load.
    def __init__(self, path):
        self.config_path = Path(path)
        json_handle = self.config_path.open("r")
        json = load(json_handle)
        self.update( json )

    ## transforms a relative path to an absolute path assuming a context of the configurations parent directory.
    #  @param self the instance of the object that is invoking this method.
    #  @param input the path to resolve to an absolute path.
    #  @returns the absolute path of the given URL.
    def _relative_path(self, input:str) -> str:
        if not input: return input
        return (self.config_path.parent / input).resolve()

    
    ## Gets a value from the configuration.
    #  @param self the instance of the object that is invoking this method.
    #  @param path_components the path to retrieve from the JSON.
    #  @param default_value the default value to return if the path is not found.
    #  @returns the value of JSON leaf.
    def get_path(self, path_components:list[str], default_value:Any=None) -> Any:

        context = self
        for component in path_components:
            context = context.get(component, None)
            if context is None:
                break
        
        if context is None and default_value:
            context = default_value

        return context
    

    ## Same as `get` but assumes the retrieved value is a file system path that needs resolving.
    #  @param self the instance of the object that is invoking this method.
    #  @param path_components the path to retrieve from the JSON.
    #  @param default_value the default value to return if the path is not found.
    #  @returns the value of JSON leaf.
    def get_file_from_path(self, path_components:list[str], default_value:Any=None) -> Path:
        value = self.get_path(path_components, default_value)
        return self._relative_path(value) if value else None
    

    ## Sets a path in the JSON map.
    #  @note never used / tested - revisit this if required.
    #  @param self the instance of the object that is invoking this method.
    #  @param path_components the path to set in the JSON.
    #  @param value the value to assign this leaf.
    def set_path(self, path_components:list[str], value:Any) -> None:
        context = self
        final_key = context[-1]
        path_components = path_components[:-1]
        for component in path_components:
            new_context = context.get(component, {})
            context[component] = new_context
            context = new_context
        context[final_key] = value
    

    ## The password the ELF binary expects to release its internal flag.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def elf_password(self) -> str:
        return self.get_path([ "elf-password" ], None)
    

    ## An ordered list of flags in this binary.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def flags(self) -> list[str]:
        return self.get_path([ "flags" ], None)


    ## Where we should build the ELF internal 64-bit code.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def elf64_build_path(self) -> str:
        return self.get_file_from_path( [ "build-paths", "elf64" ], None)
    

    ## Where we should build the ELF wrapper 32-bit code.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def elf32_build_path(self) -> str:
        return self.get_file_from_path( [ "build-paths", "elf32" ], None)
    

    ## The location that we should build the final message.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def final_mesage_build_path(self) -> str:
        return self.get_file_from_path( [ "build-paths", "final-message" ], None)
    

    ## Template for the third flag message.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def flag3_message_file(self) -> str:
        return self.get_file_from_path( [ "flag3-message" ], None)
    

    ## Wrapper that merges the third flag with the third-flag message.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    def flag3_message(self) -> ModifiedContent:
        return ModifiedContent(self.flag3_message_file, {
            "INSERT-FLAG3-HERE": self.flags[2]
        })
    
    
    ## Template for the message in the final flag of the CTF.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def final_message_file(self) -> str:
        return self.get_file_from_path( [ "final-message" ], None)
    

    ## Wrapper that merges the final flag with the final message template.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    def final_message(self) -> ModifiedContent:
        return ModifiedContent(self.final_message_file, {
            "INSERT-PASSPHRASE-HERE": self.flags[3]
        })
    

    ## Location that we should build the flag3 zip file.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def flag3_zip_build_path(self) -> str:
        return self.get_file_from_path( [ "build-paths", "flag3-zip" ], None)
    

    ## The PDF that defines the basic outline of the "hidden" PDF layer
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def hidden_layer_base(self) -> str:
        return self.get_file_from_path( [ "hidden-layer", "base" ], None)
    

    ## The location that the QR code should be blatted into on the hidden base layer.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def qr_rectangle(self) -> list[int, int, int, int]:
        return self.get_path( [ "hidden-layer", "qr-rectangle" ], None)
    
    ## The page that the QR code should be blatted into on the hidden layer.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def qr_page(self) -> int:
        return self.get_path( [ "hidden-layer", "qr-page" ], None)
    
    ## The color used to stroke rectangles in the QR code.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def qr_stroke(self) -> int:
        return self.get_path( [ "hidden-layer", "qr-stroke" ], None)
    
    ## The colour used to fill rectangles in the QR code.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def qr_fill(self) -> int:
        return self.get_path( [ "hidden-layer", "qr-fill" ], None)
    
    ## The message template to place in the QR code.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def qr_message_file(self) -> str:
        return self.get_file_from_path( [ "hidden-layer", "qr-message" ], None)
    
    ## Wrapper to merge the second flag into the QR message.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    def qr_message(self) -> ModifiedContent:
        return ModifiedContent(self.qr_message_file, {
            "INSERT-FLAG2-HERE": self.flags[1]
        })
    
    ## The location to inject the image in the hidden layer.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def image_rectangle(self) -> list[int, int, int, int]:
        return self.get_path( [ "hidden-layer", "image-rectangle" ], None)
    
    ## The image to place on the hidden layer.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def data_image(self) -> str:
        return self.get_file_from_path( [ "hidden-layer", "image-path" ], None)
       
    ## The page to inject the image onto in the hidden layer.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def image_page(self) -> int:
        return self.get_path( [ "hidden-layer", "image-page" ], None)

    ## The location to build the hidden layer.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def hidden_layer_build_path(self) -> str:
        return self.get_file_from_path( [ "build-paths", "hidden-layer-pdf" ], None)
    
    ## The place to drop the built CV file.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def final_build_path(self) -> str:
        return self.get_file_from_path( [ "build-paths", "final-cv" ], None)
    
    ## The location of the actual CV content.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the value of the property.
    @property
    def actual_cv(self) -> str:
        return self.get_file_from_path( [ "cv-path" ], None)
    

    ## The location to use for CV release builds
    #  @param self the instance of the object that is invoking this method.
    #  @returns the directory in which the final CV build artifact should be placed. 
    @property
    def release_directory(self) -> str:
        return self.get_file_from_path(  [ "build-paths", "release-directory" ], "../releases")
    

    ## The pattern used to name the final outputs from the build process.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the directory in which the final CV build artifact should be placed. 
    @property
    def release_file_fmt(self) -> str:
        return self.get_path( [ "release-format" ], "cv--{timestamp}--{ctf}.pdf")
    

    ## Determines a release file path for the CV.
    #  @param self the instance of the object that is invoking this method.
    #  @param timestamp the date and time the file was created.
    #  @param ctf_enabled whether the CTF is embedded in this version of the CV.
    #  @returns a Path object expressing where the built content should be stored.
    def release_path(self, timestamp:datetime, ctf_enabled:bool) -> Path:

        self.release_directory.mkdir(parents=True, exist_ok=True)
        
        return self.release_directory / self.release_file_fmt.format(
            timestamp = timestamp.strftime("%Y-%m-%d-%H-%M-%S"),
            ctf="with-ctf" if ctf_enabled else "no-ctf"
        )


