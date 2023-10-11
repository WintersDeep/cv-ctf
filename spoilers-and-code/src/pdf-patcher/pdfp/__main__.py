
# If this file is being invoked as the main entry point (and it really should be)
if __name__ == "__main__":

    from logging import basicConfig, DEBUG, INFO, WARN, ERROR

    from pdfp.pdf_patcher_args import PdfPatcherArguments
    from pdfp.pdf_patcher import PdfPatcher

    argument_parser = PdfPatcherArguments()
    arguments = argument_parser.parse_args()

    basicConfig(level=arguments.logging_level)

    application = PdfPatcher()
    application.run(arguments)
