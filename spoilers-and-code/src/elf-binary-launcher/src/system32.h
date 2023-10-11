#ifndef CVCTF_SYSTEM_H
#define CVCTF_SYSTEM_H

// = Wrapper for `int 0x80` invocations.
//
// Because we are not using the standard library we'll have to talk to the kernel directly via
// syscalls. This acts as a C/ASM bridge for making those syscalls.
//
// For more information see the documentation.

// useful reference(s) for opcodes:
// https://chromium.googlesource.com/chromiumos/docs/+/master/constants/syscalls.md#x86-32_bit


/// System call identifier for `mmap2`
#define _32BIT_MMAP2 0xc0


// Protection mechanisms for `mmap()`
// -------------------------------

/// No data access is allowed.
#define PROT_NONE	0x0

/// Read access is allowed.
#define PROT_READ	0x1 

/// Write access is allowed. Note that this value assumes PROT_READ also.
#define PROT_WRITE	0x2

/// This value is allowed, but is equivalent to PROT_READ.
#define PROT_EXEC	0x4


// Flags for `mmap()`
// -------------------------------

/// Share changes.
#define MAP_SHARED          0x01

/// Changes are private.
#define MAP_PRIVATE         0x02

/// Share changes and validate
#define MAP_SHARED_VALIDATE 0x03 

/// Interpret addr exactly.
#define MAP_FIXED           0x10

/// Map given file.
#define MAP_FILE            0x00

/// Don't use a file.
#define MAP_ANONYMOUS       0x20

/// Do not zero init ANONYMOUS map operation
#define MAP_UNINITIALIZED 0x4000000


// Constant returned if the MAP call fails.
#define MAP_FAILED ((void*) -1)


/// Uses the interrupt for [`mmap`](https://man7.org/linux/man-pages/man2/mmap.2.html) (x86) to map virtual memory.
//  @param address the address to map memory to, if this is NUL kernel will decide.
//  @param length the size of the memory to allocate at the specified address.
//  @param memory_protections memory protection mechanisms to apply (read/write/execute) - see `PROT_`.
//  @param flags flags associated with how memory is assigned (see spec and `MAP_`).
//  @param fd the memory file to copy into memory, ignored if MAP_ANONYMOUS but should be set to -1 for legacy purposes.
//  @param offset offset into memory file @p fd to copy into memory, ignored if MAP_ANONYMOUS but should be set to 0.
//  @returns This function returns `MAP_FAILED` if the call fails, else the address of the allocated memory.
void* _32bit_mmap2(void *address, unsigned int length, int memory_protections, int flags, int fd, unsigned int offset);



/// System call identifier for `exit`
#define _32BIT_EXIT 0x01


/// Uses the interrupt for [`exit`](https://man7.org/linux/man-pages/man2/exit.2.html) (x86) to terminate the process.
//  @param exit_code the exit code that the user is supplying, usually zero.
void _32bit_exit(int exit_code);




#endif // CVCTF_SYSTEM_H