
# python3 imports
from argparse import ArgumentParser
from pathlib import Path

# third-party imports
from fitz import PDF_ENCRYPT_KEEP

# project imports
from pdfp.actions.base import PatchActionBase
from pdfp.common import PdfDocument


## Creates a version layered PDF file 
#  Recursively saves multiple PDF documents as layers in a PDF file.
class VersionLayeredPDF(PatchActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "version-layered-pdf"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "inserts a rectangle into the document (for testing)."


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `PdfPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('out_file', metavar="PDF-OUT", type=Path, help="The location to write the new PDF with integrity values patched.")
        argument_parser.add_argument('pdf', metavar="PDF", type=argument_parser.PdfType, nargs="+", help="A layer in the PDF version history (earliest first).")


    ## The PDF document data was loaded from.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the current PDF document data is being loaded from.
    @property
    def pdf(self) -> PdfDocument:
        return self.arguments.pdf
    

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = PatchActionBase.ExitSuccess

        self.log.info(f"Building layered PDF at '{self.arguments.out_file}'.")
        
        try:

            save_kwargs = {}
            output_pdf = PdfDocument(None)

            for pdf_layer in self.arguments.pdf:
            
                # apply layer
                if output_pdf.page_count:
                    del output_pdf[0:output_pdf.page_count] # delete all the pages and attachments
                for filename in output_pdf.embfile_names():
                    output_pdf.embfile_del(filename)

                output_pdf.insert_pdf(pdf_layer) # add pdf and copy attachments
                for filename in pdf_layer.embfile_names():
                    file = pdf_layer.embfile_get(filename)
                    meta = pdf_layer.embfile_info(filename)
                    output_pdf.embfile_add(meta['name'], file, meta['filename'], meta['ufilename'], meta['desc'])

                # save and update save mode.
                output_pdf.save(self.arguments.out_file, **save_kwargs)
                output_pdf = PdfDocument(self.arguments.out_file)
                save_kwargs['encryption'] = PDF_ENCRYPT_KEEP
                save_kwargs['incremental'] = True

            self.log.info(f"Finished building layered PDF at '{self.arguments.out_file}'.")       

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = PatchActionBase.ExitRuntimeError
        
        return exit_code
