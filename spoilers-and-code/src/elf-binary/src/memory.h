#ifndef CVCTF_MEMORY_H
#define CVCTF_MEMORY_H

// = Really Simple Memory Manager
//
// Something to add some code, randomness and needless complexity to the binary. Allocates itself some memory
// via syscall to mmap/munmap which it then manages like a heap. Whilst it would be simpler to just syscall 
// memory whenever we need it - this is more 'fun'.
//
// For more information see the documentation.


/// A "row" in the page table.
//  A row in the page table is a bitfield with each bit representing a page in the memory pool.
//  Pages are sequential; the least signficant bit (0x1) represents the first page, 0x02 represents the following page,
//  0x04 the next and so on. Where a bit is set (1) the page is considered allocated. Where the sit is zero (0) the 
//  page is available for allocation. 
typedef unsigned long page_table_row;


// Basic Memory Pool configuration

/// The size of a page in the memory pool.
#define POOL_PAGE_SIZE                  ((unsigned long) 256UL )

/// The number of pages that are in the memory pool.
#define POOL_PAGE_COUNT                 ((unsigned long) ( (1024 * 1024) / POOL_PAGE_SIZE ) )

/// The total size of a memory pool measured in bytes.
#define POOL_BYTE_SIZE                  ((unsigned long) (POOL_PAGE_SIZE * POOL_PAGE_COUNT) )



// Useful memory pool information

/// The number of pages that each row can keep track (assuming 8-bits per byte).
#define PAGE_TABLE__ENTRIES_PER_ROW     ((unsigned long)( sizeof(page_table_row) * 8))

/// The total number of rows that a single page in the memory managed can store (if filled to capacity).
#define PAGE_TABLE__ROWS_PER_PAGE       ((unsigned long)( POOL_PAGE_SIZE / sizeof(page_table_row) ) ) 

/// The total number of page table rows (`page_table_row` above) required to map the state of an entire memory pool.
#define PAGE_TABLE__ROW_COUNT           ((unsigned long)( POOL_PAGE_COUNT / PAGE_TABLE__ENTRIES_PER_ROW) )

/// The total number of page table sections (`page_table_section` below) required to map the state of the entire memory pool.
#define PAGE_TABLE__SECTION_COUNT       ((unsigned long)( PAGE_TABLE__ROW_COUNT / PAGE_TABLE__ROWS_PER_PAGE) ) // the total number of allocations needed to build a table big enough to track all usable memory.



/// A section in the page table.
//  A `page_table_section` object is sized to fit within a page of the memory pool, so in many contexts section and page can 
//  be read interchangably. The object itself is just a fixed size array of rows (`page_table_row` above).
typedef page_table_row page_table_section[PAGE_TABLE__ROWS_PER_PAGE];



/// Memory pool
//  Structure for describing and managing a memory-pool (a region of memory that can be used as heap/dynamic storage).
typedef struct _MemoryPool
{
    /// The base address of the memory pool.
    //  The location from which the memory pool starts, and the address of the first assignable page.
    void* base_address;

    /// A sequential list of pointers to pages within the pool that compose the page table.
    //  The page table keeps track of regions of the pool that have been allocated for use. Each bit with-in the table
    //  represents a page, with 0 indicating that page is free and 1 that the page is allocated.
    page_table_section* page_table[PAGE_TABLE__SECTION_COUNT];

} MemoryPool;



/// Creates a new memory pool.
//  @returns a @ref MemoryPool structure describing the created memory pool. Success of the call should be checked
//    by asserting that the `base_address` field has been populated. When this value is zero (0x0000000000000000)
//    the call failed.
MemoryPool   create_memory_pool();

/// Destroys / releases an entire memory pool.
//  @param memory_pool the memory pool that you wish to release/destroy.
//  @returns an integer indicating the success of the operation directly from to [`munmap`](https://linux.die.net/man/2/munmap)
unsigned int        destroy_memory_pool(MemoryPool* memory_pool);

/// Allocates memory from the given pool.
//  @param memory_pool the memory pool that you wish to allocate memory in.
//  @param length the size of the buffer that you wish the allocator to provision for you.
//  @returns a pointer to the allocated buffer on success, or `0` on failure.
void*               allocate_memory(MemoryPool* memory_pool, unsigned long length);

/// Releases memory from the given pool.
//  @param memory_pool the memory pool that you wish to release memory in.
//  @param memory_address the address of the memory that you are releasing.
void                release_memory(MemoryPool* memory_pool, void* memory_address);



#endif // CVCTF_MEMORY_H