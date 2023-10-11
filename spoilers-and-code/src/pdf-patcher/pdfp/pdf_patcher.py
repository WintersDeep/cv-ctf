# python3 imports
from argparse import Namespace

## The PDF application
#  Acts as a wrapper for the tools/actions this package contains.
class PdfPatcher(object):
    

    ## Runs the application.
    #  @param self the instance of the object that is invoking this method.
    #  @param arguments the arguments that the application was invoked with.
    def run(self, arguments:Namespace) -> None:

        # create an instance of the action and invoked it.
        action_instance = arguments.action_class(arguments)
        exit( action_instance() )

