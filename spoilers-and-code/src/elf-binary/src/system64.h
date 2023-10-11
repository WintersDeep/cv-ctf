#ifndef CVCTF_SYSTEM_H
#define CVCTF_SYSTEM_H


// = Wrapper for `syscall` invocations.
//
// Because we are not using the standard library we'll have to talk to the kernel directly via
// syscalls. This acts as a C/ASM bridge for making those syscalls.
//
// For more information see the documentation.

// useful reference(s) for opcodes:
// https://chromium.googlesource.com/chromiumos/docs/+/master/constants/syscalls.md#x86_64-64_bit
// https://hackeradam.com/x86-64-linux-syscalls/


/// System call identifier for `read`
#define SYSCALL_READ   0x00

/// Uses the SYSCALL [`read`](https://linux.die.net/man/2/read) (x86-64) to read from a file descriptor.
//  @param fd the file descriptor to read bytes from.
//  @param buf the buffer to write bytes read from the file descriptor @p fd to.
//  @param count the number of bytes to read from @p fd into @p buf.
//  @returns the number of bytes written or `0` on error.
char sys_read(unsigned fd, const char *buf, unsigned count);



/// System call identifier for `write`
#define SYSCALL_WRITE  0x01


/// Uses the SYSCALL [`write`](https://linux.die.net/man/2/write) (x86-64) to write to a file descriptor.
//  @param fd the file descriptor to write bytes to.
//  @param buf the buffer to write to the file descriptor @p fd.
//  @param count the number of bytes to write from @p buf into @p fd.
//  @returns the number of bytes written or `-1` on error.
int sys_write(unsigned fd, const char *buf, unsigned count);



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
#define MAP_ANONYMOUS   0x20

/// Ensure mapping is in 32bit address space.
#define MAP_32BIT 0x40

/// Do not zero init ANONYMOUS map operation
#define MAP_UNINITIALIZED 0x4000000


// Constant returned if the MAP call fails.
#define MAP_FAILED ((void*) -1)


/// System call identifier for `mmap`
#define SYSCALL_MMAP   0x09


/// Uses the SYSCALL [`mmap`](https://man7.org/linux/man-pages/man2/mmap.2.html) (x86-64) to map virtual memory.
//  @param address the address to map memory to, if this is NUL kernel will decide.
//  @param length the size of the memory to allocate at the specified address.
//  @param memory_protections memory protection mechanisms to apply (read/write/execute) - see `PROT_`.
//  @param flags flags associated with how memory is assigned (see spec and `MAP_`).
//  @param fd the memory file to copy into memory, ignored if MAP_ANONYMOUS but should be set to -1 for legacy purposes.
//  @param offset offset into memory file @p fd to copy into memory, ignored if MAP_ANONYMOUS but should be set to 0.
//  @returns This function returns `MAP_FAILED` if the call fails, else the address of the allocated memory.
void* sys_mmap(void *address, unsigned long length, int memory_protections, int flags, int fd, unsigned long offset);



/// System call identifier for `munmap`
#define SYSCALL_MUNMAP 0x0b

/// Uses the SYSCALL [`munmap`](https://man7.org/linux/man-pages/man2/munmap.2.html) (x86-64) to unmap virtual memory.
//  @param address the virtual memory address that we are unmapping.
//  @param length the size of the memory allocated at the specified address.
//  @returns This function returns `0` if the call was successful, else it returns `1`.
signed int sys_munmap(void *address, unsigned long length);



/// System call identifier for `exit`
#define SYSCALL_EXIT   0x3c


/// Uses the SYSCALL [`exit`](https://linux.die.net/man/2/exit) (x86-64) to exit the current process immediatly.
//  @param error_code the error code to return from the process.
void sys_exit(int error_code);



// Flags for getrandom
//---------------------

/// Don't block and return EAGAIN instead
#define GRND_NONBLOCK       0x0001

/// Use the /dev/random pool instead of /dev/urandom
#define GRND_RANDOM         0x0002


/// System call identifier for `getrandom`
#define SYSCALL_GETRANDOM   0x13e 

/// Uses the SYSCALL `[getrandom](https://man7.org/linux/man-pages/man2/getrandom.2.html)` (x86-64) to fill a buffer with random data.
//  @param buffer pointer to buffer to full with random data.
//  @param size size of @p buffer measured in bytes.
//  @param flags flags controlling the manner in which random is generated (see above).
//  @returns the number of random bytes placed into @p buffer by this call. This may not always be the quantity requested (but will never be more).
unsigned int sys_getrandom(char* buffer, long size, long flags);



/// Rlimit idenfifier for cpu time in milliseconds.
#define	RLIMIT_CPU      0

/// Rlimit idenfifier for maximum file size.
#define	RLIMIT_FSIZE    1

/// Rlimit idenfifier for data size
#define	RLIMIT_DATA     2

/// Rlimit idenfifier for stack size.
#define	RLIMIT_STACK    3

/// Rlimit idenfifier for core file size.
#define	RLIMIT_CORE     4

/// Rlimit idenfifier for resident set size.
#define	RLIMIT_RSS      5

/// Rlimit idenfifier for locked-in-memory address space.
#define	RLIMIT_MEMLOCK  6

/// Rlimit idenfifier for number of processes
#define	RLIMIT_NPROC    7

/// Rlimit idenfifier for number of open files.
#define	RLIMIT_NOFILE   8

/// Rlimit idenfifier for address space limit.
#define RLIMIT_AS       9


/// System call identifier for `getrlimit`
#define SYSCALL_GETRLIMIT 0x61


/// Structure that recieves the result of a call from `getrlimit` calls.
typedef struct rlimit_ {

    /// The soft (current) limit.
    unsigned long rlim_cur;

    /// The hard (potential/permitted) limit you can ask for.
    unsigned long rlim_max; 
} rlimit;  


/// Uses the SYSCALL [`getrlimit`](https://man7.org/linux/man-pages/man2/getrlimit.2.html)(x86-64) to examine process resource limits.
//  Useful for debugging, not expected to be used in any final binary
//  @param resource the identifier of the resource that we are querying.
//  @param rlimit pointer to a structure to receive the result of the query.
//  returns 0 on success or -1 on failure.
signed int sys_getrlimit(unsigned long resource, rlimit* rlimit);








#endif // CVCTF_SYSTEM_H