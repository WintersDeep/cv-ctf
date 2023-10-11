
# If this file is being invoked as the main entry point (and it really should be)
if __name__ == "__main__":

    from logging import basicConfig, DEBUG, INFO, WARN, ERROR

    from ebp.elf_binary_patcher_args import ElfBinaryPatcherArguments
    from ebp.elf_binary_patcher import ElfBinaryPatcher

    argument_parser = ElfBinaryPatcherArguments()
    arguments = argument_parser.parse_args()

    basicConfig(level=arguments.logging_level)

    application = ElfBinaryPatcher()
    application.run(arguments)
