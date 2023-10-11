
# python3 imports
from argparse import ArgumentParser
from pathlib import Path
from tempfile import NamedTemporaryFile
from subprocess import run
from glob import iglob
from os import listdir
from re import compile as regex_compile, IGNORECASE, MULTILINE
from fnmatch import translate

# project imports
from cv.common.paths import Paths
from cv.actions.base import CvActionBase
from cv import build_steps


## Exports this repositories code for public Github.
#  This function is designed to take a copy of the source of this repository and provide
#  some safe-guards against publishing unexpected content (personal information such as the
#  cv itself, configuration information, etc). Its very temperamental by design and makes no
#  effort to help resolve issues to limit scope for accidental disclosures.
class ExportPublicAction(CvActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "export-public"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "exports a public snapshot of this repository."

    ## The name of the branch that we publish
    GitBranchName = "master"


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `CvAppArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('-o' ,'--export-directory', type=Path, required=True,
            help="The location that exported source should placed." )
        
    
    ## This function gets the directory we should export in.
    #  It is fairly tempermental, but deisgn.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a directory that is safe to export into.
    def get_export_directory(self):

        export_directory = Path(self.arguments.export_directory).absolute().resolve()
        
        self.log.info(f"Checking the export directory '{export_directory}'.")       

        # the directory must exist - we don't autocreate to avoid situations where I place content
        # in an unexpected places (or think its worked when I am looking at 'the wrong thing')
        if not export_directory.exists():
            raise RuntimeError(f"The export directory '{export_directory}' must exist - it doesn't.")
        
        # make sure it is actually a directory.
        if not export_directory.is_dir():
            raise RuntimeError(f"The export directory '{export_directory}' must be a directory - it isn't.")
        
        # make sure the directory is empty - if this doesn't work and there was content there previously
        # this might not be obvious - we only want to publish complete exports.
        for path in export_directory.iterdir():
            if path.is_dir() and path.name == ".git":
                # we allow .git as the most likely use case for this will be to checkout the current public copy,
                # nuke its content and apply the "latest version" over the top.
                continue
            raise RuntimeError(f"The export directory '{export_directory}' must be empty - it isn't (.git directory is permitted).")

        return export_directory

    ## Runs a command against the git repository.
    #  @param self the instance of the object that is invoking this method.
    #  @param args the arguments with which to run this command.
    #  @returns the finished git process.
    def git_command(self, *args):
        git_process = run([ "git", *args ], capture_output=True, encoding='utf-8',  cwd=Paths.ProjectRoot)

        if len(git_process.stderr) != 0 or git_process.returncode != 0:
            raise RuntimeError(f"Git command failed; {git_process.stderr}")
        
        return git_process

    ## Checks that the repository has no unstaged changes.
    #  @param self the instance of the object that is invoking this method.
    def check_git_repository(self):

        self.log.info(f"Checking the git repository is ready.")       

        git_process = self.git_command("status", "--porcelain")
        
        if len(git_process.stdout) != 0:
            raise RuntimeError("The .git repository is not ready. Please ensure there are no unstaged changes.")
           
        git_process = self.git_command("branch", "--show-current")
        git_branch = git_process.stdout.strip()

        if git_branch != self.GitBranchName:
            raise RuntimeError(f"The .git repository is not on the correct branch; expected '{self.GitBranchName}' but got '{git_branch}'.")


    ## copies the source to the target location.
    #  @param self the instance of the object that is invoking this method.
    #  @param target the location to copy the source to.
    def export_repository(self, target):

        self.log.info(f"Copying source to export directory")       

        with NamedTemporaryFile("r") as export_temp:
            git_process = self.git_command("archive", "--output", export_temp.name, self.GitBranchName)
            tar_process = run(["tar", "-xf", export_temp.name, "-C", target], capture_output=True)
            if tar_process.returncode != 0 or len(tar_process.stderr) != 0:
                raise RuntimeError(f"tar export failed; {tar_process.stderr}")


    ## Checks for documents that might contain sensative information thats not wanted in the public repository.
    #  This is more complex than glob to handle case-insenstive pattern matching.
    #  @param self the instanec of the object that is invoking this method.
    #  @param glob the glob pattern to search for.
    #  @param name the name of the documents that are being searched for (for logging)
    #  @param directory the directory in which to search for these documents.
    #  @param known_safe_documents document paths that we include but we know are safe to share.
    def check_for_unexpected_documents(self, glob, name, directory, known_safe_documents=[]):
        
        file_regex = regex_compile(translate(glob), IGNORECASE)
        root_directory = directory.absolute().resolve()

        self.log.info(f"... looking for {name}")       

        def __check_directory__(target):
            for content in Path(target).iterdir():

                relative_path = content.relative_to(root_directory)

                if content.is_dir():
                    self.log.debug(f"   ... Stepping into sub-directory: {relative_path}")
                    __check_directory__(content)

                elif file_regex.match( str(content) ):

                    if not str( relative_path ) in known_safe_documents:
                        raise RuntimeError(f"Exported content contained an unexpected data; {relative_path}")
                    
                    else:
                        self.log.debug(f"   ... Spotted acceptable risk: {relative_path}")

                else:
                    self.log.debug(f"   ... Not in scope of regex: {relative_path}")

        __check_directory__(root_directory)


    ## Checks for unexpected PDF disclosures:
    #  Mainly checking that I am not pushing my actual CV into the public repository.
    #  @param self the instance of the object that is inokving this method.
    #  @param target the directory in which the export copy of the repository can be found.
    def check_for_unexpected_pdfs(self, target):
        self.check_for_unexpected_documents(    
            "**/*.pdf", "PDF documents", target, [
                # no safe PDF's in export content.
        ])


    ## Checks for unexpected JSON disclosures:
    #  Using JSON for configuration - make sure copies of the config weren't in the export.
    #  @param self the instance of the object that is inokving this method.
    #  @param target the directory in which the export copy of the repository can be found.
    def check_for_unexpected_json(self, target):
        self.check_for_unexpected_documents(    
            "**/*.json", "JSON documents", target, [
                # no safe JSON in export content.
        ])
        
    
    ## Checks for unexpected text disclosures:
    #  Internal messages, this is less PII and more protecting the flag/secrets.
    #  @param self the instance of the object that is inokving this method.
    #  @param target the directory in which the export copy of the repository can be found.
    def check_for_unexpected_text(self, target):
        self.check_for_unexpected_documents(    
            "**/*.txt", "TXT documents", target, [
                "spoilers-and-code/src/elf-binary-patcher/requirements.txt",
                "spoilers-and-code/src/pdf-patcher/requirements.txt",
                "spoilers-and-code/src/cv-builder/requirements.txt",
        ])
        self.check_for_unexpected_documents(    
            "**/*.text", "TEXT documents", target, [])


    ## Checks for unexpected image disclosures:
    #  CTF images, again less PII and more protecting flags.. did have some headshots in the past too.
    #  @param self the instance of the object that is inokving this method.
    #  @param target the directory in which the export copy of the repository can be found.
    def check_for_unexpected_images(self, target):
        self.check_for_unexpected_documents("**/*.png", "PNG documents", target, [
            "spoilers-and-code/docs/walk-through/images/flag2-example.png"
        ])
        self.check_for_unexpected_documents("**/*.jpe?g", "JPG documents", target, [])
        self.check_for_unexpected_documents("**/*.gif", "GIF documents", target, [])


    ## Checks for unexpected build directories:
    #  Build directories may contain unprotected secrets or copies of the CV in build.
    #  @param self the instance of the object that is inokving this method.
    #  @param target the directory in which the export copy of the repository can be found.
    def check_for_unexpected_build_directories(self, target):
        self.check_for_unexpected_documents("**/build", "build directories", target, 
                                            [
        ])


    ## Checks directories we really do not want to release.
    #  These shouldn't come over as they are stored seperately anyhow (or are build artifacts/temp files), and
    #  the bits in here we care about _should_ be caught by other checks, but no harm in a little paranoia.
    #  @param self the instance of the object that is inokving this method.
    #  @param target the directory in which the export copy of the repository can be found.
    def check_sensitive_directories(self, target):
        self.log.info(f"... known sensitive paths")       
        for path in [
            "spoilers-and-code/src/assets",
            "spoilers-and-code/src/releases",
            "spoilers-and-code/src/pdf-patcher/test-data",
        ]:
            if (target / path).exists():
                raise RuntimeError(f"Sensitive directory; should not be in public release - {path}")


    ## performs a number of checks to attempt to safe gaurd against information we don't want being published ending up in the public repository.
    #  @param self the instance of the object that is inokving this method.
    #  @param target the directory in which the export copy of the repository can be found.
    def heuristic_leak_check(self, target):
        self.log.info(f"Checking export for potentially unintended diclosures...")       
        self.check_for_unexpected_pdfs(target)
        self.check_for_unexpected_json(target)
        self.check_for_unexpected_text(target)
        self.check_for_unexpected_images(target)
        self.check_for_unexpected_build_directories(target)
        self.check_sensitive_directories(target)


    ## Lists any new files ending up in the repository.
    #  The heuristic checks are good for guarding against files we expect, this is designed as a final warning - it tries to draw attention
    #  to new files we are adding (that might not be accomodated by heuristics). After the initial push this list should be short so by reviewing
    #  it we should be able to avoid some risk of pushing PII to github.
    #  @param self the instance of the object that is inokving this method.
    #  @param target the directory in which the export copy of the repository can be found.
    def list_new_files(self, target):

        new_file_mask = regex_compile("^\?\? (?P<filename>.*)$", MULTILINE)

        git_process = run([ "git", "status", "--porcelain" ], capture_output=True, encoding='utf-8',  cwd=target)

        if len(git_process.stderr) != 0 or git_process.returncode != 0:
            self.log.warn(f"Cannot list new files; {git_process.stderr.strip()}")
        else:
            
            new_files = new_file_mask.findall(git_process.stdout)
            
            if new_files:

                def __print_files__(item, dir_content=None):
                    
                    item_relative_path = item.relative_to(target)
                    if item.is_dir():
                        for subitem in item.iterdir():
                            __print_files__(subitem, dir_content or item)
                    elif dir_content:
                        dir_relative_path = item.relative_to(dir_content)
                        self.log.warn(f"({item_relative_path}) {dir_relative_path}")
                    else:
                        self.log.warn(item_relative_path)

                self.log.warn("DANGER: The following files are new - make sure they are fit for public release before pushing.")
                
                for item in new_files: 
                    __print_files__( target / item )
                

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = CvActionBase.ExitRuntimeError

        with NamedTemporaryFile() as elf_fh:
            
            try:

                self.check_git_repository()

                export_directory = self.get_export_directory()

                self.export_repository(export_directory)
                self.heuristic_leak_check(export_directory)
                self.list_new_files(export_directory)

                exit_code = CvActionBase.ExitSuccess

                self.log.info(f"Finished exporting source code.")       

            except RuntimeError as ex:
                self.log.error(ex)
        
        return exit_code
