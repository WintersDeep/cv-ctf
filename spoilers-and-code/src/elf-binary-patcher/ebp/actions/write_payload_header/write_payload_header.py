
# python3 imports
from argparse import ArgumentParser, FileType
from typing import TypeVar
from random import randint
from datetime import datetime

# project imports
from ebp.actions.base import InPatchActionBase


## Self type for the @ref PayloadConfiguration object.
PayloadConfigurationType = TypeVar('PayloadConfigurationType', bound='PayloadConfiguration')


## The configuration of the payload to write.
class PayloadConfiguration(object):
     
    ## Creates a new instance of the object.
    #  @param self the instance of the object that is invoking this method.
    #  @param payload the payload to write to the header file.
    #  @param entry the offset into the binary that execution should start.
    def __init__(self, payload:bytes, entry:int) -> PayloadConfigurationType:
        self.payload = payload
        self.entry = entry
        self.fizz = None
        self.fizz_up = None
        self.buzz = None
        self.buzz_up = None


    ## Modifies the internal data payload for "fizz-buzz" unpacking.
    #  @param self the instance of the object that is invoking this method.
    #  @param fizz the interval on which to add "fizz_up" to the xor key.
    #  @param fizz_up the value to add to the xor key on "fizz" interval.
    #  @param buzz the interval on which to add "buzz_up" to the xor key.
    #  @param buzz_up the value to add to the xor key on "buzz" interval.
    def apply_fizzbuzz(self, fizz:int, fizz_up:int, buzz:int, buzz_up:int) -> None:

        xor_key = 1
        new_payload = []

        for index, byte_ in enumerate(self.payload):

            if index % fizz == 0: xor_key += fizz_up
            if index % buzz == 0: xor_key += buzz_up
            if index % fizz != 0 and index % buzz != 0:
                xor_key += 1
            xor_key &= 0xff

            new_payload.append(byte_ ^ xor_key)
        
        self.payload = bytes(new_payload)
        self.fizz = fizz
        self.fizz_up = fizz_up
        self.buzz = buzz
        self.buzz_up = buzz_up


    ## Applies a random fizzbuzz unpack to the payload.
    #  @param self the instance of the object that is invoking this method.
    def apply_random_fizzbuzz(self):
        self.apply_fizzbuzz(
            randint(1, 255),
            randint(1, 255),
            randint(1, 255),
            randint(1, 255)
        )



## "Write Payload Header" action
#  Writes the payload header that is used to build the 32-bit wrapper/launcher.
class WritePayloadHeaderAction(InPatchActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "write-payload-header"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "Generates the `payload.h` header used in the `elf-binary-launcher` project."


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `ElfBinaryPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        InPatchActionBase.configure_cli_parser(argument_parser)
        argument_parser.add_argument("-o", "--out-file", type=FileType("w"), 
            help="The literal seed used to initialise the PRNG which disguises the embedded hidden string (usually should be omitted to be random).")


    ## Writes a line out to the header file.
    #  @param self the instance of the object that is invoking this method.
    #  @param message the message string to write out.
    def write_line(self, message:str="") -> None:
         self.arguments.out_file.write(f"{message}\n");


    ## Writes out the headers... header/preable.
    #  @param self the instance of the object that is invoking this method.
    #  @param config the configuration of the payload.
    def write_header(self, config:PayloadConfiguration):
        self.write_line("/***")
        self.write_line(" payload.h - definitions for the internal 64-bit crackme binary.")
        self.write_line(" THIS FILE IS AUTOMATICALLY GENERATED - DO NOT ALTER IT AND EXPECT THOSE CHANGES TO PERSIST.")
        self.write_line(f"     binary-source: {self.elf.path}.")
        self.write_line(f"         output-to: {self.arguments.out_file.name}")
        self.write_line(f"      generated-at: {datetime.utcnow()}")
        self.write_line(f"      payload-size: {len(config.payload)} bytes (0x{len(config.payload)})")
        self.write_line("*/")
        self.write_line()

    ## Writes out the binary payload blob
    #  @param self the instance of the object that is invoking this method.
    #  @param config the configuration of the payload.
    def write_payload_byte_array(self, config:PayloadConfiguration) -> None:

        tab = " " * 4
        payload_bytes_per_line = 32
        payload_size = len(config.payload)

        self.write_line("// the obfuscated binary payload injected into .text and unpacked into memory.")
        # self.write_line("const unsigned char payload_data[] = {")

        # for i in range(0, payload_size, payload_bytes_per_line):
        #         chunk_end = min(i + payload_bytes_per_line, payload_size)
        #         eol = "" if chunk_end == payload_size -1 else ","
        #         chunk_bytes = config.payload[i:chunk_end]
        #         byte_string = ", ".join( f"0x{b:02x}" for b in chunk_bytes )
        #         self.write_line(f"{tab}{byte_string}{eol}")

        # self.write_line("};")
        self.write_line("#define PAYLOAD_BYTES_DEFINITION(VARNAME) {  \\")
        self.write_line(f"{tab}asm volatile(\\")
        self.write_line(f'{tab}"{tab}call end_of_function;" \\')
        self.write_line(f'{tab}"{tab}payload_bytes:" \\')
        for i in range(0, payload_size, payload_bytes_per_line):
                  chunk_end = min(i + payload_bytes_per_line, payload_size)
                  chunk_bytes = config.payload[i:chunk_end]
                  byte_string = ", ".join( f"0x{b:02x}" for b in chunk_bytes )
                  self.write_line(f'{tab}"{tab}{tab}.byte {byte_string};" \\')
        self.write_line(f'{tab}"{tab}end_of_function:" \\')
        self.write_line(f'{tab}"{tab}{tab}pop %0;" \\')
        self.write_line(f'{tab}: "=m" (VARNAME) \\')
        self.write_line(f'{tab}); /* PAYLOAD_BYTES_DEFINITION */  \\')
        self.write_line("}")
        self.write_line()


    ## Writes out the entry point for the binary payload.
    #  @param self the instance of the object that is invoking this method.
    #  @param config the configuration of the payload.
    def write_entry_point(self, config:PayloadConfiguration) -> None:
        self.write_line("// offset into the payload that execution should start.")
        self.write_line(f"#define PAYLOAD_ENTRY (0x{config.entry:08x})\n")
        self.write_line()


    ## Writes the size of the payload.
    #  @param self the instance of the object that is invoking this method.
    #  @param config the configuration of the payload.
    def write_payload_size(self, config:PayloadConfiguration) -> None:
        self.write_line("// the length of the payload in bytes.")
        self.write_line(f"#define PAYLOAD_SIZE (0x{len(config.payload):08x})\n")
        self.write_line()
 
     ## Writes the size of the payload.
    #  @param self the instance of the object that is invoking this method.
    #  @param config the configuration of the payload.
    def write_fizzbuzz_values(self, config:PayloadConfiguration) -> None:
        self.write_line("// parameter used by fizzbuzz unpack - fizz interval.")
        self.write_line(f"#define FIZZ (0x{config.fizz:02x})")
        self.write_line()
        self.write_line("// parameter used by fizzbuzz unpack - fizz increment.")
        self.write_line(f"#define FIZZ_UP (0x{config.fizz_up:02x})")
        self.write_line()
        self.write_line("// parameter used by fizzbuzz unpack - buzz interval.")
        self.write_line(f"#define BUZZ (0x{config.buzz:02x})")
        self.write_line()
        self.write_line("// parameter used by fizzbuzz unpack - buzz increment.")
        self.write_line(f"#define BUZZ_UP (0x{config.buzz_up:02x})\n")
        self.write_line()


    ## Invokes this action on an ELF file.
    #  This action will take protected strings from the binary and inject code to build the required strings.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = self.__class__.ExitSuccess

        self.log.info(f"Creating `payload.h` at '{self.arguments.out_file.name}' for '{self.elf.path}'.")
        
        try:

            payload_section = self.elf.get_section_containing(self.elf.entry)
            payload_mem_start = payload_section.header.sh_addr
            payload_mem_size = payload_section.header.sh_size
            payload_mem_bytes = self.elf.read(payload_mem_start, payload_mem_size)
            payload_mem_entry = self.elf.entry - payload_mem_start

            config = PayloadConfiguration(payload_mem_bytes, payload_mem_entry)
            config.apply_random_fizzbuzz()

            for writer in [
                self.write_header,
                self.write_payload_byte_array,
                self.write_entry_point,
                self.write_payload_size,
                self.write_fizzbuzz_values
            ]:
                 writer(config)

            bytes_written = f" ({self.arguments.out_file.tell()} bytes)" if self.arguments.out_file.seekable() else ""

            self.log.info(f"Finished writing `payload.h` at '{self.arguments.out_file.name}'{bytes_written}.")


        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = self.__class__.ExitRuntimeError
        
        return exit_code