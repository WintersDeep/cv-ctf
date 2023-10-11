// project includes
#include "system64.h"
#include "memory.h"


#define POOL_ALLOCATION_FLAGS MAP_PRIVATE|MAP_ANONYMOUS|MAP_UNINITIALIZED|MAP_32BIT

/// Selects random offsets in the memory pool to store the page table.
//  Offsets are set in the `MemoryPool::page_table` as page indices. These offsets will have to be 
//  relocated to pointers once `MemoryPool::base_address` has been assigned.
//  @param memory_pool the memory pool to assign offsets for.
//  @returns On success returns `1`, else on failure returns `0`. This function does not currently
//     provide error information on failure; but for reference it has two failure modes:
//       - `sys_getrandom` did not provide enough random data on request.
//       -  random offsets always contained duplicate values after `maximum_attempts` times.
signed long _allocate_page_table_section_offsets(MemoryPool* memory_pool)
{
    const unsigned int maximum_attempts = 100;
    unsigned long random_source[PAGE_TABLE__SECTION_COUNT];
    const unsigned int RANDOM_SOURCE_SIZE = sizeof(unsigned long) * PAGE_TABLE__SECTION_COUNT;

    for(unsigned int attempt = 0; attempt < maximum_attempts; attempt++)
    {
        unsigned int bytes_generated = sys_getrandom((void*) &random_source[0], RANDOM_SOURCE_SIZE, 0);

        if(bytes_generated != RANDOM_SOURCE_SIZE) 
            return 0;
        
        for(unsigned int offset_index = 0; offset_index < PAGE_TABLE__SECTION_COUNT; offset_index++)
        {
            unsigned long offset = (random_source[offset_index] & (unsigned long) -1) % POOL_PAGE_COUNT;

            memory_pool->page_table[offset_index] = (void*) offset;

            for(unsigned int check_index = 0; check_index < offset_index; check_index++)
            {
                if(memory_pool->page_table[offset_index] == memory_pool->page_table[check_index])
                    goto generate_new_set_of_offsets;
            }
        }

        return 1;

generate_new_set_of_offsets: /* semi-colon for label */ ;
    }

    return 0;
}


/// Given a page index returns a pointer to the table row that holds its allocation state information.
//  Note that the caller will still need to determine the specific bit for the requested page; this can
//  be easily calculated with `index % PAGE_TABLE__ENTRIES_PER_ROW`.
//  @remarks NOTE that this method does not check if the given index is actually in the pool - its is 
//    expected that callers to this method are internal, and that only indicies within a valid range 
//    will be provided. Use of invalid values leads to undefined behaviour.
//  @param memory_pool the memory pool which contains the relevant page that is identified by @p index.
//  @param index the index of the page to find the relevant table row for.
//  @returns A pointer to the `page_table_row` that contains state information for the specified page.
page_table_row* _page_index_to_page_table_row(MemoryPool* memory_pool, unsigned long index)
{
    unsigned long row_index = index / PAGE_TABLE__ENTRIES_PER_ROW;
    unsigned long section_index = row_index / PAGE_TABLE__ROWS_PER_PAGE;
    unsigned long section_offset = row_index % PAGE_TABLE__ROWS_PER_PAGE;
    page_table_section* section = memory_pool->page_table[ section_index ];
    return &(*section)[section_offset];
}


/// Marks the page identified by the given index as allocated (assigned for use).
//  @remarks NOTE that this method does not check if the given index is actually in the pool, or if
//    the page itself has already been allocated. Its is expected that callers to this method are 
//    internal, and that only valid indicies will be provided. Use of invalid values leads to undefined
//    behaviour.
//  @param memory_pool the memory pool which contains the relevant page that is identified by @p index.
//  @param index the index of the page that is to be set as allocated.
void _mark_page_index_allocated(MemoryPool* memory_pool, unsigned long index)
{
    page_table_row* table_row = _page_index_to_page_table_row(memory_pool, index);
    unsigned long row_bit = index % PAGE_TABLE__ENTRIES_PER_ROW;
    page_table_row allocate_mask = (1UL << row_bit);
    *table_row |= allocate_mask;
}


/// Marks the page identified by the given index as free (unassigned and not in use).
//  @remarks NOTE that this method does not check if the given index is actually in the pool, or if
//    the page itself is already free. Its is expected that callers to this method are internal, and 
//    that only valid indicies will be provided. Use of invalid values leads to undefined behaviour. 
//  @param memory_pool the memory pool which contains the relevant page that is identified by @p index.
//  @param index the index of the page that is to be set as unallocated / free.
void _mark_page_index_free(MemoryPool* memory_pool, unsigned long index)
{
    page_table_row* table_row = _page_index_to_page_table_row(memory_pool, index);
    unsigned long row_bit = index % PAGE_TABLE__ENTRIES_PER_ROW;
    page_table_row free_mask = ~(1UL << row_bit);
    *table_row &= free_mask;
}


/// Determines if the page identified by the given index is allocated / in use.
//  @remarks NOTE that this method does not check if the given index is actually in the pool, or if
//    the page itself is already free. Its is expected that callers to this method are internal, and 
//    that only valid indicies will be provided. Use of invalid values leads to undefined behaviour.
//  @param memory_pool the memory pool which contains the relevant page that is identified by @p index.
//  @param index the index of the page to check for allocation.
//  @returns This method returns non-`0` if the page indified by @p index is allocated, else it returns `0`.
unsigned int _is_page_index_allocated(MemoryPool* memory_pool, unsigned long index)
{
    page_table_row* table_row = _page_index_to_page_table_row(memory_pool, index);
    unsigned long row_bit = index % PAGE_TABLE__ENTRIES_PER_ROW;
    page_table_row check_mask = (1UL << row_bit);
    return (*table_row & check_mask) > 0;
}


/// Creates a new memory pool.
//  @returns a @ref MemoryPool structure describing the created memory pool. Success of the call should be checked
//    by asserting that the `base_address` field has been populated. When this value is zero (0x0000000000000000)
//    the call failed. The method has two potential failure modes which are:
//      - `_allocate_page_table_section_offsets` was unable to generate offsets for the page table.
//      - `sys_mmap` was unable to allocate memory to be used as a buffer for this pool.
MemoryPool create_memory_pool()
{
    const int NO_FILE_OFFSET = 0;
    const int NO_FILE_DESCRIPTOR = -1;

    MemoryPool new_pool = { 0 };

    // generate offsets for the page table
    if( _allocate_page_table_section_offsets(&new_pool) == 1 )
    {
        // allocate memory for the memory pool
        void* buffer = sys_mmap(0, POOL_BYTE_SIZE, PROT_READ|PROT_WRITE, 
            POOL_ALLOCATION_FLAGS, NO_FILE_DESCRIPTOR, NO_FILE_OFFSET);
        
        if (buffer != MAP_FAILED)
        {
            new_pool.base_address = buffer;
            unsigned long page_table_offsets[PAGE_TABLE__SECTION_COUNT];

            // relocate the offsets for the page table to their final pointer values.
            for(unsigned int page_table_index = 0; page_table_index < PAGE_TABLE__SECTION_COUNT; page_table_index++)
            {
                unsigned long offset = (unsigned long)new_pool.page_table[page_table_index];
                page_table_section* page_address = buffer + (offset * POOL_PAGE_SIZE);
                new_pool.page_table[page_table_index] = page_address;
                page_table_offsets[page_table_index] = offset;

                for(unsigned int row_index = 0; row_index < PAGE_TABLE__ROWS_PER_PAGE; row_index++)
                     (*new_pool.page_table[page_table_index])[row_index] = 0x00;
            }

            // mark pages used by the page table as allocated.
            for(unsigned int page_table_index = 0; page_table_index < PAGE_TABLE__SECTION_COUNT; page_table_index++)
                _mark_page_index_allocated( &new_pool, page_table_offsets[page_table_index] );

        }
    }

    return new_pool;
}


/// Destroys / releases an entire memory pool.
//  @param memory_pool the memory pool that you wish to release/destroy.
//  @returns an integer indicating the success of the operation directly from to [`munmap`](https://linux.die.net/man/2/munmap)
unsigned int destroy_memory_pool(MemoryPool* memory_pool)
{
    return sys_munmap(memory_pool->base_address, POOL_BYTE_SIZE);
}


/// Allocates memory from the given pool.
//  @param memory_pool the memory pool that you wish to allocate memory in.
//  @param length the size of the buffer that you wish the allocator to provision for you.
//  @returns a pointer to the allocated buffer on success, or `0` on failure. This method
//     does not return information about the cause of a failure, but has one failure modes:
//        - all pages are currently allocated.
void* allocate_memory(MemoryPool* memory_pool, unsigned long length)
{
    unsigned long random_offset = 0;
    void* assigned_memory = 0;

    if(length <= POOL_PAGE_SIZE)
    {
        // this might fail in part or entirely (unlikely, but it could); however  in context 
        // I dont think I really care - the random allocation is nice, but not essential. Not
        // worth crashing over at this point.
        sys_getrandom((void*) &random_offset, sizeof(random_offset), 0);
        
        random_offset %= POOL_PAGE_COUNT;

        for(unsigned int index = 0; index < POOL_PAGE_COUNT; index++)
        {   
            unsigned long page_offset = (random_offset + index) % POOL_PAGE_COUNT;

            if(_is_page_index_allocated(memory_pool, page_offset) == 0)
            {
                assigned_memory = memory_pool->base_address + (page_offset * POOL_PAGE_SIZE);
                _mark_page_index_allocated(memory_pool, page_offset);
                break;
            }
        }
        
    }
    
    return assigned_memory;
}


/// Write random junk into the page.
//  This destroys and data that was in the allocated page. We use random rather
//  than zero as if you are not paying attenion is might look like the page is 
//  still in use.
//  @param page a pointer to the start of the page.
__attribute__((always_inline))
__attribute__((optimize("O0")))
inline void _scramble_page(char* page) {

    const int RANDOM_SOURCE_SIZE = 64;
    char random_source[RANDOM_SOURCE_SIZE];

    for(unsigned int i = 0; i < POOL_PAGE_SIZE; i++) {
        if(i % RANDOM_SOURCE_SIZE == 0)
            sys_getrandom((void*) &random_source[0], RANDOM_SOURCE_SIZE, 0);  
        *(page + i) = random_source[i % RANDOM_SOURCE_SIZE];
    }

}


/// Releases memory from the given pool.
//  @remarks attempting to release memory not owned by the pool has no effect. Releasing
//    memory that is unallocated is also safe (at least in terms of the pools state).
//  @param memory_pool the memory pool that you wish to release memory in.
//  @param memory_address the address of the memory that you are releasing (if this does not
//    align with a page boundry. The page from which the address resides in will be released).
void release_memory(MemoryPool* memory_pool, void* memory_address)
{
    if (memory_address > memory_pool->base_address)
    {
        unsigned long memory_offset = memory_address - memory_pool->base_address;

        if (memory_offset < POOL_BYTE_SIZE)
        {
            unsigned long page_offset = memory_offset / POOL_PAGE_SIZE;

            void* page_base = memory_pool->base_address + (page_offset * POOL_PAGE_SIZE);
            _mark_page_index_free(memory_pool, page_offset);
            _scramble_page(page_base);
        }
    }
}