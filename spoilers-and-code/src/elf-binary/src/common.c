#include "common.h"
#include "system64.h"

/// Writes the content of the given buffer to the given file descriptor.
//  @param fd file descriptor to write to.
//  @param buffer the buffer to write to standard out.
//  @param size the number of bytes to write from @p buffer to standard out.
//  @returns 0 on success, else error code.
int _write(signed int fd, const char* buffer, unsigned int size)
{
    unsigned int consumed = 0;

    while(consumed < size)
    {
        signed int result = sys_write(fd, buffer + consumed, size);
        if (result < 0) return result;
        consumed += result;
    }

    return 0;
}

/// Writes the content of the given buffer to standard out.
//  @param buffer the buffer to write to standard out.
//  @param size the number of bytes to write from @p buffer to standard out.
//  @returns 0 on success, else error code.
int stdout(const char* buffer, unsigned int size)
{
    return _write(FD_STDOUT, buffer, size);
}

/// Writes the content of the given buffer to standard error.
//  @param buffer the buffer to write to standard error.
//  @param size the number of bytes to write from @p buffer to standard error.
//  @returns the number of bytes written or `-1` on failure.
int stderr(const char* buffer, unsigned int size)
{
    return _write(FD_STDERR, buffer, size);
}

/// Reads a line of input from standard input.
//  @param buffer the buffer to read into.
//  @param size the maximum number of bytes to read into the given buffer.
//  @returns the number of bytes read.
signed int readline_stdin(char* buffer, signed int size)
{
    char byte;
    signed int index = 0;

    while(index < size)
    {
        if(sys_read(FD_STDIN, &byte, 1) == 0 || byte == '\n') break;
        *(buffer + index++) = byte;
    }

    return index;
}