#include "system64.h"

/// Uses the SYSCALL [`exit`](https://linux.die.net/man/2/exit) (x86-64) to exit the current process immediatly.
//  @param error_code the error code to return from the process.
void sys_exit(int error_code)
{

    asm volatile
    (
        "syscall"
        : 
        : "a"(SYSCALL_EXIT), "D"(error_code)
        : "rcx", "r11", "memory" 
    );
}


/// Uses the SYSCALL [`read`](https://linux.die.net/man/2/read) (x86-64) to read from a file descriptor.
//  @param fd the file descriptor to read bytes from.
//  @param buf the buffer to write bytes read from the file descriptor @p fd to.
//  @param count the number of bytes to read from @p fd into @p buf.
//  @returns the number of bytes read or `0` on error.
char sys_read(unsigned fd, const char *buf, unsigned count)
{
    char bytes_read;

    asm volatile
    (
        "syscall"
        : "=a"(bytes_read)
        : "a"(SYSCALL_READ), "D"(fd), "S"(buf), "d"(count)
        : "rcx", "r11", "memory"
    );
    
    return bytes_read;
}


/// Uses the SYSCALL [`write`](https://linux.die.net/man/2/write) (x86-64) to write to a file descriptor.
//  @param fd the file descriptor to write bytes to.
//  @param buf the buffer to write to the file descriptor @p fd.
//  @param count the number of bytes to write from @p buf into @p fd.
//  @returns the number of bytes written or `-errno` on error.
int sys_write(unsigned fd, const char *buf, unsigned count)
{
    unsigned bytes_written;

    asm volatile
    (
        "syscall"
        : "=a"(bytes_written)
        : "a"(SYSCALL_WRITE), "D"(fd), "S"(buf), "d"(count)
        : "rcx", "r11", "memory"
    );
    
    return bytes_written;
}


/// Uses the SYSCALL [`mmap`](https://man7.org/linux/man-pages/man2/mmap.2.html) (x86-64) to map virtual memory.
//  @param address the address to map memory to, if this is NUL kernel will decide.
//  @param length the size of the memory to allocate at the specified address.
//  @param memory_protections memory protection mechanisms to apply (read/write/execute) - see `PROT_`.
//  @param flags flags associated with how memory is assigned (see spec and `MAP_`).
//  @param fd the memory file to copy into memory, ignored if MAP_ANONYMOUS but should be set to -1 for legacy purposes.
//  @param offset offset into memory file @p fd to copy into memory, ignored if MAP_ANONYMOUS but should be set to 0.
//  @returns This function returns `MAP_FAILED` if the call fails, else the address of the allocated memory.
void* sys_mmap(void *address, unsigned long length, int memory_protections, int flags, int fd, unsigned long offset)
{
    void* mapped_memory;

    asm volatile
    (
        "movq %[flags],  %%r10;"
        "movq %[fd],     %%r8;"
        "movq %[offset], %%r9;"
        "syscall;"
        : "=a"(mapped_memory)
        : "a"(SYSCALL_MMAP), "D"(address), "S"(length), "d"(memory_protections), 
            [flags]  "rm"((unsigned long)flags),
            [fd]     "rm"((unsigned long)fd),
            [offset] "rm"(offset)
        : "rcx", "r8", "r9", "r10", "r11", "memory" 
    );

    return mapped_memory;
}



/// Uses the SYSCALL [`munmap`](https://man7.org/linux/man-pages/man2/munmap.2.html) (x86-64) to unmap virtual memory.
//  @param address the virtual memory address that we are unmapping.
//  @param length the size of the memory allocated at the specified address.
//  @returns This function returns `0` if the call was successful, else it returns `1`.
signed int sys_munmap(void *address, unsigned long length)
{
    signed int return_value;

    asm volatile
    (
        "syscall"
        : "=a"(return_value)
        : "a"(SYSCALL_MUNMAP), "D"(address), "S"(length)
        : "rcx", "r11", "memory" 
    );

    return return_value;
}


/// Uses the SYSCALL [`getrandom`](https://man7.org/linux/man-pages/man2/getrandom.2.html) (x86-64) to fill a buffer with random data.
//  @param buffer pointer to buffer to full with random data.
//  @param size size of @p buffer measured in bytes.
//  @param flags flags controlling the manner in which random is generated (see above).
//  @returns the number of random bytes placed into @p buffer by this call. This may not always be the quantity requested (but will never be more).
unsigned int sys_getrandom(char* buffer, long size, long flags)
{
    unsigned int bytes_generated;

    asm volatile
    (
        "syscall"
        : "=a"(bytes_generated)
        : "a"(SYSCALL_GETRANDOM), "D" (buffer), "S" (size), "d" (flags)
        : "rcx", "r11", "memory"
    );
    
    return bytes_generated;
}


/// Uses the SYSCALL [`getrlimit`](https://man7.org/linux/man-pages/man2/getrlimit.2.html)(x86-64) to examine process resource limits.
//  Useful for debugging, not expected to be used in any final binary
//  @param resource the identifier of the resource that we are querying.
//  @param rlimit pointer to a structure to receive the result of the query.
//  returns 0 on success or -1 on failure.
signed int sys_getrlimit(unsigned long resource, rlimit* rlimit)
{
    signed int result;

    asm volatile
    (
        "syscall"
        : "=a"(result)
        : "a"(SYSCALL_GETRLIMIT), "D" (resource), "S" (rlimit)
        : "rcx", "r11", "memory"
    );
    
    return result;
}