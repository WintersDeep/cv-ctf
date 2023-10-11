
#include "system32.h"
#include "payload.h"


/** this builds a very simple assembly stub at [ptr] that contains the following x86 instructions:

    0: 9a 44 33 22 11 33 00    call   0x33:code64_entry
    7: c3                      ret

    this code performs a far jump to the code at [code64_entry], which has the effect of switching
    the CPU from 32bit to 64bit mode - here there be dragons.
    
    @param ptr the location to build the 64bit transition.
    @param code64_entry the location of the 64bit code entry point.
*/
void build_64bit_transition(char* ptr, void* code64_entry)
{
    // far call instruction (9a 44 33 22 11 33 00    call   0x33:code64_entry)
    ptr[0] = 0x9a;
    *((unsigned int*)(ptr+1)) = (unsigned int)code64_entry;
    ptr[5] = 0x33;
    ptr[6] = 0x00;

    // return instruction  (c3  ret)
    ptr[7] = 0xc3;
}

/** Small stub that invokes the 64-bit transition code written by `build_64bit_transition`.
    @param transition_address the location that we placed the opcodes to handle transitioning to 64-bit
*/
void hand_off_to_64bit(void* transition_address)
{
    void (*transition_to_64bit)() = (void (*) ())transition_address;
    transition_to_64bit();
}


/** 
    This function unpacks the binary payload using a fizz-buzz-esque de-obfuscation mechanism.
    @param dst the location to place the unpacked content.
    @param src the location to read content from.
    @param length the length of the data at @p src
    @note FIZZ/BUZZ intervals are random per build and imported via #define from `payload.h`. The impacts a "fizz", "buzz", or "fizzbuzz" is
      also random and defined there.

    > "I'm sorry to ask, but we have to run you through a quick programming excercise, are you familiar with fizz buzz... its company policy".
    
    This one's for you Martin.
*/
void fizz_buzz_unpack(unsigned char* dst, const unsigned char* src, unsigned long length)
{
    unsigned long xor_key = 1;

    for(unsigned long i = 0; i < length; i++)
    {
        if(i % FIZZ == 0) xor_key += FIZZ_UP;
        if(i % BUZZ == 0) xor_key += BUZZ_UP;
        if(i % FIZZ != 0 && i % BUZZ != 0)
            xor_key += 1;
        xor_key &= 0xff;

        dst[i] = src[i] ^ xor_key;
    }
}

/**
    This function retrieves address of the encoded payload bytes.
    This is messy, but I want to nuke all data sections so I'm using inline assembler to inject the payload into this function
    as a raw byte stream. This way I can be sure its in .text and pul out a local label address to return to the caller.
*/
const void const* payload_bytes_ptr()
{
    void * payload_bytes;
    PAYLOAD_BYTES_DEFINITION(payload_bytes);
    return payload_bytes;
}


/**
    Checks if this looks like a 64-bit CPU in 32-bit mode.
    Does this by checking the current code segment register value is 0x23- would expect this to be 0x73 (0x1b for Windows) if its 32-bit native.
*/
int is_64bit_cpu_in_32bit_mode()
{
    unsigned int cs_register;

    asm volatile(
        "movw %%cs, %0;" 
        : "=m" (cs_register)
    );

    return cs_register == 0x23;
}


/**
    Main entry point
*/
void _start()
{

    if(is_64bit_cpu_in_32bit_mode())
    {
        // allocate some memory to inject the 64-bit code into using mmap2 syscall.
        void* ptr = _32bit_mmap2(0, PAYLOAD_SIZE + 9, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS | MAP_UNINITIALIZED, -1, 0);

        if(ptr != (void*) 0)
        {
            // calculate some offsets into the allocated memory.
            void* entry_point = ptr + PAYLOAD_ENTRY;
            fizz_buzz_unpack(ptr, payload_bytes_ptr(), PAYLOAD_SIZE);

            void* bridge = ptr + PAYLOAD_SIZE;
            build_64bit_transition(bridge, entry_point);        
            hand_off_to_64bit(bridge);
        }
    }

    _32bit_exit(255);
}