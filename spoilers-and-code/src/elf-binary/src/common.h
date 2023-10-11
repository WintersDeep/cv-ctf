#ifndef CVCTF_COMMON_H
#define CVCTF_COMMON_H

// = Common Library
//
// A collection of odds-and-sods for things that we want to do, and don't fit elsewhere.
//
// For more information see the documentation.

/// Standard in file descriptor.
#define FD_STDIN  0

/// Standard out file descriptor.
#define FD_STDOUT 1

/// Standard error file descriptor.
#define FD_STDERR 2




/// Writes the content of the given buffer to standard out.
//  @param buffer the buffer to write to standard out.
//  @param size the number of bytes to write from @p buffer to standard out.
//  @returns the number of bytes written or `-1` on failure.
int stdout(const char* buffer, unsigned int size);

/// Writes the content of the given buffer to standard error.
//  @param buffer the buffer to write to standard error.
//  @param size the number of bytes to write from @p buffer to standard error.
//  @returns the number of bytes written or `-1` on failure.
int stderr(const char* buffer, unsigned int size);


/// Reads a line of input from standard input.
//  @param buffer the buffer to read into.
//  @param size the maximum number of bytes to read into the given buffer.
//  @returns the number of bytes read or `-1` on failure
signed int readline_stdin(char* buffer, signed int size);


#endif // CVCTF_COMMON_H