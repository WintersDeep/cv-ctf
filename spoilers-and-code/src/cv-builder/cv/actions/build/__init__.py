
# python3 imports
from argparse import ArgumentParser, FileType
from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime
from shutil import copyfile
from hashlib import sha256

# project imports
from cv.common.paths import Paths
from cv.actions.base import CvActionBase
from cv import build_steps

## Builds the entire CV based on a build configuration.
#  the general command expected to use to build the software
#  @tbd as this is the end of the build chain its been left really unfinished once it all worked - it could really do with 
#    being tidied up.
class Build(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "build"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "build the entire CV from the group up."

    ## The default output path if omitted.
    DefaultConfigurationFile = Paths.AssetsDirectory / "configuration.json"


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('-c' ,'--configuration', type=Path,
            default=cls.DefaultConfigurationFile,
            help="The location of the configuration file." 
        )
        

    ## Calculates the SHA256 checksum of a file.
    #  Used for the release history table.
    #  @param self the instance of the object that is invoking the method.
    #  @param file the path to the file that you want a checksum for.
    #  @returns the hex digest of the file.
    def calculate_sha256(self, file:Path) -> str:
                
        sha256_ = sha256()

        with file.open("rb") as cv_handle:
            while True:
                chunk = cv_handle.read(65535)
                if not chunk: break
                sha256_.update(chunk)

        return sha256_.hexdigest()

    ## Builds the CV from the ground up based on a configuration.
    #  @param self the instance of the object that is invoking this method.
    #  @param config the current configuration of the module.
    #  @returns the exit code for the process (was the CV actually built...)
    def build_cv(self, config:build_steps.BuildConfiguration) -> int:

        exit_code = CvActionBase.ExitSuccess

        with config.qr_message() as qr_message, \
             config.flag3_message() as flag3_message, \
             config.final_message() as final_message, \
             NamedTemporaryFile() as hidden_layer_temp:
            
            hidden_layer_temp.close()

            flag3_zip_content = {
                "README": flag3_message,
                "flag4": config.elf32_build_path,
                "final-message.zip": config.final_mesage_build_path
            }

            final_message_zip_content = {
                "message.txt": final_message 
            }
            
            self.log.info(f"Building CV.")
            
            try:
                
                self.run_build_steps([
                    ("building internal 64-bit binary", build_steps.BuildCrackmeInternal(config.elf_password, config.flags[2], config.elf64_build_path)),
                    ("patching internal binary strings", build_steps.BuildCrackmePatchString(config.elf64_build_path, config.elf64_build_path)),
                    ("patching internal binary integrity", build_steps.BuildCrackmePatchIntegrity(config.elf64_build_path, config.elf64_build_path)),
                    ("generating 32-bit launcher payload data", build_steps.GenerateLaunchpayloadHeader(config.elf64_build_path)),
                    ("building 32-bit launcher", build_steps.BuildCrackmeLauncher(config.elf32_build_path)),
                    ("stripping 32-bit launcher", build_steps.BuildCrackmeStripInternal(config.elf32_build_path, config.elf32_build_path)),
                    ("creating final message zip", build_steps.MakeEncryptedZip(config.final_mesage_build_path, config.flags[2],  final_message_zip_content)),
                    ("creating flag3 zip container", build_steps.MakeEncryptedZip(config.flag3_zip_build_path, config.flags[0] + " " + config.flags[1],  flag3_zip_content)),
                    ("inserting qr code into hidden layer", build_steps.PdfInsertBlockQrCode(
                        config.hidden_layer_base, hidden_layer_temp.name,
                        *config.qr_rectangle, qr_message.read_text(), config.qr_page, 
                        config.qr_stroke, config.qr_fill
                    )),
                    ("inserting image+zip into hidden layer", build_steps.PdfAddImageWithTrailingData(
                        hidden_layer_temp.name,  config.hidden_layer_build_path,
                        *config.image_rectangle, config.data_image, config.flag3_zip_build_path,
                        config.image_page
                    )),
                    ("layering PDFs", build_steps.MakeVersionLayeredPdf([
                        config.hidden_layer_build_path,
                        config.actual_cv
                    ], config.final_build_path)),
                ])

                self.log.info(f"Finished building CV; final release written to '{config.final_build_path}'.")       

            except RuntimeError as ex:
                self.log.error(ex)
                exit_code = CvActionBase.ExitRuntimeError

        return exit_code


    ## Copies a build of the CV (both with and without CTF) to the build directory.
    #  @param self the instance of the object that is invoking this method.
    #  @param config the current configuration of the module.
    def make_release(self, config:build_steps.BuildConfiguration):
         
        release_time = datetime.utcnow()

        self.log.info(f"Copying final assets to releases...")       
        copyfile( config.final_build_path, config.release_path(release_time, True) )
        copyfile( config.actual_cv, config.release_path(release_time, False) )


    ## Updates the version history table to include the current release.
    #  @param self the instance of the object that is invoking this method.
    #  @param config the current configuration of the module.
    def update_history_file(self, config:build_steps.BuildConfiguration):

        release_time = datetime.utcnow()

        release_history = Paths.SrcRootDirectory.parent.parent / "release-history.md" 

        with release_history.open("a+") as release_history_handle:
            history_time = release_time.strftime("%Y-%m-%d %H:%M:%S")
            cv_ctf_sha256 = self.calculate_sha256(config.final_build_path)
            cv_pdf_sha256 = self.calculate_sha256(config.actual_cv)
            release_history_handle.write(f"| {history_time} | {cv_ctf_sha256} | {cv_pdf_sha256} |\n")


    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        #
        # @tbd this module really needs to be cleaned up.
        #

        config = build_steps.BuildConfiguration(self.arguments.configuration)
        
        exit_code = self.build_cv(config)

        if exit_code == self.ExitSuccess:
            self.make_release(config)
            self.update_history_file(config)
        
        return exit_code
