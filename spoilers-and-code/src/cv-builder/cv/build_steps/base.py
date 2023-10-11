# python imports
from abc import ABC, abstractmethod
from sys import executable
from subprocess import Popen, PIPE, STDOUT, CompletedProcess

# project imports
from cv.common import Environment

## The base of a build step.
class BuildStep(ABC):
    

    ## Executes an the `ebp` python application.
    #  @param args the positional arguments provided to `Popen`
    #  @param kwargs the keyword arguments provided to `Popen`
    #  @returns a CompletedProcess describing the output of the process.
    def elf_patcher(self, *args:list, **kwargs:dict) -> CompletedProcess:
        return self.python_module('ebp', *args, **kwargs)

    ## Executes an the `pdfp` python application.
    #  @param args the positional arguments provided to `Popen`
    #  @param kwargs the keyword arguments provided to `Popen`
    #  @returns a CompletedProcess describing the output of the process.
    def pdf_patcher(self, *args:list, **kwargs:dict) -> CompletedProcess:
        return self.python_module('pdfp', *args, **kwargs)


    ## Executes an python module using the current interpreter.
    #  @param args the positional arguments provided to `Popen`
    #  @param kwargs the keyword arguments provided to `Popen`
    #  @returns a CompletedProcess describing the output of the process.
    def python_module(self, module_name, *args:list, **kwargs:dict) -> CompletedProcess:
        args = list(args)
        args[0] = [ executable, '-m', module_name ] + args[0]
        return self.execute(*args, **kwargs)


    ## Executes a command and prints its output.
    #  @param self the instance of the object that is invoking this method.
    #  @param args the positional arguments provided to `Popen`
    #  @param kwargs the keyword arguments provided to `Popen`
    #  @returns a CompletedProcess describing the output of the process.
    def execute(self, *args:list, **kwargs:dict) -> CompletedProcess:

        kwargs.setdefault('stdout', PIPE)
        kwargs.setdefault('stderr', STDOUT)
        kwargs.setdefault('encoding', "utf-8")
        kwargs.setdefault('env', Environment())

        command = [ str(a) for a in args[0] ]
        popen = Popen(command, *args[1:], **kwargs)

        for line in popen.stdout:
            print(line, end="")

        return CompletedProcess(args[0], popen.wait(), None, None)
    

    ## Indicates if the process exited successfully.
    #  @remarks will also set `exit_code` on the build step instance.
    #  @param self the instance of the object that is invoking this method
    #  @param process the process that we are determining our exit success on.
    #  @returns True if the process exited successfully else False
    def ExitSuccess(self, process:CompletedProcess) -> bool:
        setattr(self, 'exit_code', process.returncode)
        return self.exit_code == 0 


    ## Invokes the build step.
    #  @param self the instance of the object that is invoking this method.
    #  @returns a boolean indicating if the build step was successful of not.
    @abstractmethod
    def __call__(self) -> bool:
        pass