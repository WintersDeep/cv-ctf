
# If this file is being invoked as the main entry point (and it really should be)
if __name__ == "__main__":

    from logging import basicConfig, DEBUG, INFO, WARN, ERROR

    from cv.cv_application_args import CvAppArguments
    from cv.cv_application import CvApp

    argument_parser = CvAppArguments()
    arguments = argument_parser.parse_args()

    basicConfig(level=arguments.logging_level)

    application = CvApp()
    application.run(arguments)
