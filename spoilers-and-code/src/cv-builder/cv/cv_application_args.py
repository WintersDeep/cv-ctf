# python3 imports
from argparse import ArgumentParser, ArgumentTypeError, Action, Namespace
from logging import DEBUG, INFO, WARN, ERROR
from pathlib import Path
from typing import TypeVar, Any

# project imports
from cv import __summary__ as application_summary
from cv.actions import available_actions

## The @ref PdfPatcherArguments `Self` type
SelfType = TypeVar('SelfType', bound='CvAppArguments')
        


## Custom parser action to catch logging level.
#  Used to handle conversion from string to integer.
class CliLoggingLevel(Action):
    
    ## The string logging levels and their related python `logging` level.
    LoggingLevels = {
        "debug": DEBUG,
        "info": INFO,
        "warn": WARN,
        "error": ERROR
    }

    ## Invoked when an arguments value is stored.
    #  @param parser the parser that took in the value.
    #  @param namespace the namespace capturing the results of the parse.
    #  @param values the values provided by the user.
    #  @option_string any associated options string.
    def __call__(self, parser:ArgumentParser, namespace:Namespace, values:Any, option_string=None) -> None:
        # note that we should be safe to draw straight from the dict all cavilear because
        # the option should be generated from `choices=Self.LoggingLevel.keys()`
       setattr(namespace, self.dest, self.LoggingLevels[values])


## Arguments for the `cv` python application
#  Extends the python native `ArgumentParser`, specialising it for the `cv` application.
class CvAppArguments(ArgumentParser):


    ## The default name of the program
    #  Override to indicate how this application is expected to be invoked - default 
    #  behaviour would result in program name being reported as `__main__.py`
    DefaultProgramName:str = "python -m cv"

    ## The description of the program
    #  Inherited from the applications summary.
    DefaultDescription:str = application_summary


    ## Instanciates a new @ref CvAppArguments object.
    #  @param self the instance of the object that is invoking this method.
    #  @param kwargs keyword arguments supplied to this objects constructor.
    def __init__(self, **kwargs) -> SelfType:

        kwargs.setdefault("prog", self.__class__.DefaultProgramName)
        kwargs.setdefault("description", self.__class__.DefaultDescription)
        super().__init__(**kwargs)

        self._build_cv_arguments()


    ## Builds the expected command line arguments.
    #  @param self the instance of the object that is invoking this method.
    def _build_cv_arguments(self) -> None:

        self.add_argument("-l", "--logging-level", type=str, 
            choices=CliLoggingLevel.LoggingLevels.keys(), default=INFO, action=CliLoggingLevel,
            help="The amount of logging that this tooling should generate.")

        actions_subparsers = self.add_subparsers(dest="action", help="the actions this tool can perform", parser_class=ArgumentParser)
        actions_subparsers.required = True

        for action in available_actions:
            action_arguments = actions_subparsers.add_parser(action.cli_command, help=action.cli_help)
            action_arguments.set_defaults(action_class=action)
            action.configure_cli_parser(action_arguments)
