#include "system32.h"

/// Uses the SYSCALL [`mmap`](https://man7.org/linux/man-pages/man2/mmap.2.html) (x86-64) to map virtual memory.
//  @param address the address to map memory to, if this is NUL kernel will decide.
//  @param length the size of the memory to allocate at the specified address.
//  @param memory_protections memory protection mechanisms to apply (read/write/execute) - see `PROT_`.
//  @param flags flags associated with how memory is assigned (see spec and `MAP_`).
//  @param fd the memory file to copy into memory, ignored if MAP_ANONYMOUS but should be set to -1 for legacy purposes.
//  @param offset offset into memory file @p fd to copy into memory, ignored if MAP_ANONYMOUS but should be set to 0.
//  @returns This function returns `MAP_FAILED` if the call fails, else the address of the allocated memory.
void* _32bit_mmap2(void *address, unsigned int length, int memory_protections, int flags, int fd, unsigned int offset)
{
    void* mapped_memory;

    asm volatile
    (
        "push %%ebp;"
        "mov %[offset], %%ebp;"
        "int $0x80;"
        "pop %%ebp;"
        : "=a"(mapped_memory)
        : "a"(_32BIT_MMAP2), "b"(address), "c"(length), "d"(memory_protections), "S"(flags), "D"(fd),
            [offset] "rm"(offset)
        : "memory"
    );

    return mapped_memory;
}



/// Uses the interrupt for [`exit`](https://man7.org/linux/man-pages/man2/exit.2.html) (x86) to terminate the process.
//  @param exit_code the exit code that the user is supplying, usually zero.
//  @remarks this call does not return - the process is terminated.
void _32bit_exit(int exit_code)
{
    asm volatile
    (
        "int $0x80;"
        : : "a"(_32BIT_EXIT), "b"(exit_code)
    );
}
