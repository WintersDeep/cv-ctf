# python3 imports
from pathlib import Path
from setuptools import setup

# local imports
from cv import (
    __version__ as application_version,
    __summary__ as application_summary
)

## path to this setup.py file
setup_file = Path(__file__)

## root directory for this project.
project_directory = setup_file.parent.resolve()

## The project root directory.
src_directory = project_directory.parent

## long description of the project.
#  @remarks loaded from the projects README.md file.
readme_md = project_directory / 'README.md'

## List of packages that this project requires
required_dependencies = [
    f"ebp    @ file://localhost/{src_directory}/elf-binary-patcher",          # used to parse/edit the ELF files.
    f"pdfp   @ file://localhost/{src_directory}/pdf-patcher",                 # used to parse/edit the PDF files.
    f"pyminizip   >=0.2.6, <0.3",                                             # used to make encrypted ZIP files.
]


# do the setup action.
setup(

    # The name of the application.
    name = 'cv',

    # The version of the application
    version = application_version,

    # A summary of the application purpose.
    description = application_summary,

    # A more verbose description of the application (loaded from README.md)
    long_description = readme_md.read_text(encoding='utf-8'),

    ## Long description MIME format.
    long_description_content_type = 'text/markdown',  # Optional (see note above)

    # Link to your project's main homepage.
    url = 'https://github.com/wintersdeep/cv-ctf',

    # Name of the developer that made the project.
    author = 'WintersDeep',

    # Email address for the developer of the project.
    author_email = 'admin@wintersdeep.com', 

    # The version of python this package is designed for.
    python_requires='>=3.9, <4',

    # List of dependencies that this module requires.
    install_requires = required_dependencies,

    # List additional URLs that are relevant to the package.
    project_urls={
        "module": "https://github.com/wintersdeep/cv-ctf/spoilers-and-code/src/cv-builder/README.md"
    }
)