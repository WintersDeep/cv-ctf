// project imports
#include "integrity.h"

/// Magic value that will be replaced in the generator with the start of the .text virtual memory space.
#define START_OF_SEGMENT_VIRTUAL_MEMORY             (0xca11ab1e0ddba115)

// magic value that will be replaced with the amount of memory required for the unchecked QWORD assignment.
#define INTEGRITY_CHECK_ALLOC_PLACEHOLD             (0x5adc01dc0ffeebad)


/// MurmurOOAT64 method (ish) - calculates the hash of the given data buffer.
//  @param data_buffer a pointer to the data to caclulate a hash of.
//  @param length the amount of data to hash from @p data_buffer.
//  @param state the current state of the hash, or if the first buffer hashed can be used as a seed value.
//  @returns the state of the hash after the given data buffer has been consumed - either use or feed back in as state.
unsigned long murmur_oaat64(const unsigned char * data_buffer, unsigned long length, unsigned long state)
{
    for (unsigned long i = 0; i < length; i++) {
        state ^= data_buffer[i];
        state *= 0x5bd1e9955bd1e995;
        state ^= state >> 47;
    }

    return state;
}


/// Calculates a hash of this binaries "predictable" contents.
//  @param state the state (or seed) used to initialise the hashing algorithm.
//  @returns the hash of the fixed content of the binary.
unsigned long calculate_binary_hash(unsigned long state, MemoryPool* memory_pool)
{

    CONTAINS_INTEGRITY_GENERATOR(NUMBER_OF_VOLATILE_QWORDS, {

        // INTEGRITY_CHECK_ALLOC_PLACEHOLD is actually going to be `(NUMBER_OF_VOLATILE_QWORDS +1) * sizeof(hash)`
        // but this will be inserted by the post-build tool and this is easier to read here, and find when patching.
        unsigned int* memory_offset_qwords = allocate_memory(memory_pool, INTEGRITY_CHECK_ALLOC_PLACEHOLD);

        if(memory_offset_qwords)
        {     
            
            char* virtual_memory_ptr;

            // ARRAY_SETUP_SIZE is has +2 to account for the end of memory and STOP entries
            //   which are added to the end of the array; assignments look like:
            //  c7 43 7f 44 33 22 11           mov    dword [rbx+0x7f],0x11223344 - 7 bytes
            #define ARRAY_SETUP_SIZE ( NUMBER_OF_VOLATILE_QWORDS + 2) * 7

            // The number of bytes required to assign the RAX register to the start of VMA
            //   48 8d 1d f9 ff ff ff          lea    rbx,[rip+0xfffffffffffffff9]
            #define ASSIGN_VIRTUAL_MEMORY_PTR_SIZE 7

            // The number of bytes required to patch the generator configuration.
            #define PATCH_SIZE ARRAY_SETUP_SIZE + ASSIGN_VIRTUAL_MEMORY_PTR_SIZE


            // reserve space in .text to patch generator - we need to build the volatile offsets array
            // and set the start of VMA. RAX will receive the address to the memory allocated for
            // volatile QWORDS and should return a pointer to the start of virtual memory for this section.
            asm volatile (
                ".fill %c[reserve_size], 1, 0x90"
                : "=b" (virtual_memory_ptr)
                : [reserve_size] "i" (PATCH_SIZE),
                                 "b" (memory_offset_qwords)
                : "memory", "cc", "rax"
            );

            unsigned int* data_length = memory_offset_qwords;

            while(*data_length != (unsigned int) -1)
            {
                state = murmur_oaat64(virtual_memory_ptr, *data_length, state);
                virtual_memory_ptr += (*data_length + sizeof(unsigned long));
                data_length++;
            }

            release_memory(memory_pool, memory_offset_qwords);
        }

        return state;

    })

}


