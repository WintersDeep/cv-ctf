#ifndef CVCTF_INTEGRITY_H
#define CVCTF_INTEGRITY_H

    #include "memory.h"

    /// The number of qwords that cannot be signed that are in the software.
    //  Post build tooling will complain if this is not correct and tell you what it should be.
    #ifndef NUMBER_OF_VOLATILE_QWORDS
    #define NUMBER_OF_VOLATILE_QWORDS 3
    #endif

    /// The hash value that should be used as a place holder for the hash of protected sections.
    //  This hash QWORD is considered volatile and will be omitted from hash checking.
    #define INTEGRITY_HASH 0xaddf00dc0ffeebed


    /// The hash value that should be used as a place holder for the hash of protected sections.
    //  Where this value is NOT volatile - it will contribute to the binary hash.
    #define INTEGRITY_SEED 0x1eaf5adca75f00d5


    /// The magic value that will be replaced by a post build tool with an XOR mask (against current hash) to produce a known value 
    //  This hash QWORD is considered volatile and will be omitted from hash checking.
    #define XOR_MASK_FOR_KNOWN_VALUE 0x5afe70bec0d3ab1e


    /// The magic value that will be replaced by a post build tool with the correct hash for a known value.
    //  This hash QWORD is considered volatile and will be omitted from hash checking.
    #define EXPECTED_MURMUR_HASH 0xfea75ba5e64b10b5


    /// The prefix used for sections that record the location of regions that need an integrity hash injected.
    // 
    //  The post-build tool will look for this prefix to determine what work it needs to do when patching the binary.
    #define HASH_PATCH_PREFIX ".hash-patch"


    /// Size of the meta data available for "other data"
    #define META_SIZE 256


    /// Structure used to store meta data for an XOR_TO_KNOWN section descriptor
    struct __attribute__((__packed__))  _xor_to_known 
    {
        /// The value that should be generated by an XOR with the current hash (assuming the hash is correct).
        unsigned long required_value;
        
        /// The seeding order that this XOR_TO_KNOWN occurs in (this must be created by a regular CONTAINS_INTEGRITY_HASH section)
        signed long order;

        /// The seeding sequence / chain that this is part of.
        char sequence_id[];
    };

    /// Structure used to store meta data for an INSERT_MURMUR section descriptor
    struct __attribute__((__packed__)) _known_murmur_hash
    {
        /// The amount of data to expected before the sequence ID in `buffer_value_and_sequence_id` (the "known value to hash").
        unsigned int size_of_data;
        
        /// The seeding order that this INSERT_MURMUR occurs in (this must be created by a regular CONTAINS_INTEGRITY_HASH section)
        signed long order;

        /// The seeding sequence / chain that this is part of.
        char buffer_value_and_sequence_id[];
    };

    /// Union that stores meta information about a hash patch entry.
    union _hash_patch_section_entry_meta
    {
        /// Used by most hash patch entry - simple raw access to the meta data.
        char raw[META_SIZE];

        /// Used by XOR_TO_KNOWN to describe a required XOR masks parameters. 
        struct _xor_to_known xor_to_known;

        struct _known_murmur_hash known_murmur_hash;

    };



    /// Structure of a hash patch section entry.
    // 
    //  This structure  records information about the location of an area that needs to be
    //  patched with the binary hash. A post build process will look for INTEGRITY_HASH and replace
    //  it with the expected hash value for the compiled binary. If the INTEGRITY_HASH is not found 
    //  in the region the patch tool will complain, so if you create a CONTAINS_INTEGRITY_HASH it must include
    //  a usage of INTEGRITY_HASH. A region may use INTEGRITY_HASH more than once.
    struct hash_patch_section_entry
    {
        /// The start of the memory region that might contain an integrity ACTION_OR_SEEDINGhash
        void*           start_of_entry;

        /// The end of the memory region that might contain an integrity hash
        void*           end_of_entry;

        /// Determines the action the hash patch will perform.
        //  These come in two "flavours" - regular actions are in the range >= 0 (N). These represent a normal hash
        //  of the binary, with the seed value being the result from the previous hash. For the lowest hash in this 
        //  range the seed will be initialised randomly (and is injected with the INTEGRITY_SEED definition). The 
        //  expected literal hash can be injected if required with the INTEGRITY_HASH definition. A given N can be 
        //  used more than once - for instance if it needs to appear in two differing branches of logic - however 
        //  a developer MUST ensure that the number of hashes encountered at each increment is correct as there is
        //  no way for the precompiler to determine this.
        //  For special use cases `hash_action` will have a negative value - see below for their usages.
        signed long     hash_action;

        /// Meta information related to this call. Used for special `hash_action` types.
        union _hash_patch_section_entry_meta meta;
    };

    
    



    /// Indicates that this a generator integrity hash entry.
    //  Usually there will only be one integrity hash generator, but not reason multiple cannot be inserted (for
    //  example maybe we inline in the future).
    #define HASH_GENERATOR -1


    /// Indicates the section wants an XOR mask that will convert the integrity hash to a known value.
    //  This is useful as, if the binary hasn't been modified it will produce a known result. If the binary has
    //  been compromsed the produce value will be random and unusable. This can be checked more creatively to
    //  avoid disclosing the hash we expect this value to have.
    #define XOR_TO_KNOWN -2


    /// Indicates the section needs a hash injected into the code for a known value.
    //  The hash is taken from a murmurooat64 seeded with the current integrity hash. Allows us to verify 
    //  a value is a known good without disclosing what that known good is.
    #define INSERT_MURMUR -3


    #ifndef STRINGIFY
        /// Converts a precompiler-number to string.
        /// 
        /// @see https://gcc.gnu.org/onlinedocs/cpp/Stringizing.html#Stringizing for more information.
        #define STRINGIFY(NUM) # NUM
    #endif // STRINGIFY

    #ifndef INDIRECT
        /// @see https://gcc.gnu.org/onlinedocs/cpp/Stringizing.html#Stringizing for more information.
        #define INDIRECT(L) STRINGIFY(L)
    #endif // INDIRECT


    //  ANNOTATE_HASH_PATCH__XXX macros all create a section annotation that describes part of the integrity system that needs patching.
    //  This macro will create a section in the ELF that reports the approximate start and end of the code region that is expected
    //  to contain the relevant code, and an integer that describes what is there. The meta information section is more loose and 
    //  its contents will depend entirely on the type of component prensent. Each XXX implementation handles a different type of META.

    /// Creates a "hash patch" annotation with a raw data meta section.
    #define ANNOTATE_HASH_PATCH__RAW(IVID, ACTION_OR_SEEDING, META)                                         \
        {                                                                                                   \
            static __attribute__( ( section(HASH_PATCH_PREFIX "." __FILE__ ":"  INDIRECT(__LINE__)) ) )     \
            struct hash_patch_section_entry _ = {                                                           \
                .start_of_entry = &&START_HASH_PATCH_ANNOTATION_NAME(IVID),                                 \
                .end_of_entry = &&END_HASH_PATCH_ANNOTATION_NAME(IVID),                                     \
                .hash_action = ACTION_OR_SEEDING,                                                           \
                .meta={ .raw = META }                                                                       \
            };                                                                                              \
        }        
        

    /// Creates a "hash patch" annotation with an XOR_TO_KNOWN data meta section.
    #define ANNOTATE_HASH_PATCH__XOR_TO_KNOWN(IVID, SEQUENCE_ID, SEEDING, REQUIRED_KNOWN)                   \
        {                                                                                                   \
            static __attribute__( ( section(HASH_PATCH_PREFIX "." __FILE__ ":"  INDIRECT(__LINE__)) ) )     \
            struct hash_patch_section_entry _ = {                                                           \
                .start_of_entry = &&START_HASH_PATCH_ANNOTATION_NAME(IVID),                                 \
                .end_of_entry = &&END_HASH_PATCH_ANNOTATION_NAME(IVID),                                     \
                .hash_action = XOR_TO_KNOWN,                                                                \
                .meta = { .xor_to_known = {                                                                 \
                    .order=SEEDING,                                                                         \
                    .required_value=REQUIRED_KNOWN,                                                         \
                    .sequence_id=SEQUENCE_ID                                                                \
                }}                                                                                          \
            };                                                                                              \
        }


    /// Creates a "hash patch" annotation with an INSERT_MURMUR data meta section.
    #define ANNOTATE_HASH_PATCH__INSERT_MURMUR(IVID, SEQUENCE_ID, SEEDING, REQUIRED_KNOWN)                  \
        {                                                                                                   \
            static __attribute__( ( section(HASH_PATCH_PREFIX "." __FILE__ ":"  INDIRECT(__LINE__)) ) )     \
            struct hash_patch_section_entry _ = {                                                           \
                .start_of_entry = &&START_HASH_PATCH_ANNOTATION_NAME(IVID),                                 \
                .end_of_entry = &&END_HASH_PATCH_ANNOTATION_NAME(IVID),                                     \
                .hash_action = INSERT_MURMUR,                                                               \
                .meta = { .known_murmur_hash = {                                                            \
                    .order=SEEDING,                                                                         \
                    .size_of_data=sizeof(REQUIRED_KNOWN) -1,                                                \
                    .buffer_value_and_sequence_id = REQUIRED_KNOWN SEQUENCE_ID                              \
                }}                                                                                          \
            };                                                                                              \
        }


    /// Determines the label name used to identify the start and end of "hash patch" regions.
    #define HASH_PATCH_ANNOTATION_NAME(IVID, TYPE) HASH_PATCH_ ## IVID ## _ ## TYPE
        
    /// Determines the label name used to identify the start of a "hash patch" regions.
    #define START_HASH_PATCH_ANNOTATION_NAME(IVID) \
        HASH_PATCH_ANNOTATION_NAME(IVID, START)

    /// Determines the label name used to identify the end of a "hash patch" regions.
    #define END_HASH_PATCH_ANNOTATION_NAME(IVID) \
         HASH_PATCH_ANNOTATION_NAME(IVID, END)


    /// Marks the boundry of code relevant to this module.
    #define INSERT_MARKED_CODE_REGION(IVID, ...)                        \
        START_HASH_PATCH_ANNOTATION_NAME(IVID):                         \
        __VA_ARGS__                                                     \
        END_HASH_PATCH_ANNOTATION_NAME(IVID): ;                         \


    /// Macro that identifies a piece of code that contains logic related to the binaries integrity hash.
    //  A post build process tool will look in these regions to replace instances of INTEGRITY_HASH with the binaries 
    //  integrity hash and INGRITY_SEED with a random integrity seed.
    #define CONTAINS_INTEGRITY_HASH(SEQUENCE_ID, SEEDING, ...) \
        INSERT_HASH_PATCH__RAW(__COUNTER__, SEEDING, SEQUENCE_ID, __VA_ARGS__)
        
    /// Macro that marks a piece of code that contains a "hash generator" the code that generates integrity hashes.
    //  A post build process tool will patch this to include information about memory and volatile qwords in the software.
    #define CONTAINS_INTEGRITY_GENERATOR(NUMBER_OF_VOLATILE_QWORDS, ...) \
        INSERT_HASH_PATCH__RAW(__COUNTER__, HASH_GENERATOR, NUMBER_OF_VOLATILE_QWORDS, __VA_ARGS__)
        

    /// Inserts a "hash patch" region.
    //  This basically does all the work CONTAINS_INTEGRITY_HASH/GENERATOR says its going to do - the indirection is required to
    //  allow propogation / multiple use of the __COUNTER__ value.
    #define INSERT_HASH_PATCH__RAW(IVID, ACTION_OR_SEEDING, META, ...)       \
        ANNOTATE_HASH_PATCH__RAW(IVID, ACTION_OR_SEEDING, META)         \
        INSERT_MARKED_CODE_REGION(IVID, __VA_ARGS__)


    /// Macro that marks a piece of code that requires an XOR that works with the current chain hash to product a known value.
    //  The build process will replace XOR_MASK_FOR_KNOWN_VALUE with a mask that can convert the current hash to a known value.
    #define REQUIRES_INTEGRITY_XOR_TO_KNOWN(SEQUENCE_ID, SEEDING, REQUIRED_KNOWN, ...) \
        INSERT_HASH_PATCH__XOR_TO_KNOWN(__COUNTER__, SEQUENCE_ID, SEEDING, REQUIRED_KNOWN, __VA_ARGS__)

    /// Inserts a "hash patch" region.
    //  This basically does all the work INSERT_HASH_PATCH__XOR_TO_KNOWN says its going to do - the indirection is required to
    //  allow propogation / multiple use of the __COUNTER__ value.
    #define INSERT_HASH_PATCH__XOR_TO_KNOWN(IVID, SEQUENCE_ID, SEEDING, REQUIRED_KNOWN, ...)       \
        ANNOTATE_HASH_PATCH__XOR_TO_KNOWN(IVID, SEQUENCE_ID, SEEDING, REQUIRED_KNOWN) \
        INSERT_MARKED_CODE_REGION(IVID, __VA_ARGS__)


    /// Macro that marks a piece of code that requires a murmur hash for an expected data value.
    //  The build process will replace EXPECTED_MURMUR_HASH with the result of hashing the known value using a 
    //  murmur oaat seeded with the current integrity hash.
    #define REQUIRES_INTEGRITY_MURMUR_HASH(SEQUENCE_ID, SEEDING, KNOWN_VALUE, ...) \
        INSERT_INTEGRITY_MURMUR_HASH(__COUNTER__, SEQUENCE_ID, SEEDING, KNOWN_VALUE, __VA_ARGS__)

    /// Inserts a "hash patch" region.
    //  This basically does all the work REQUIRES_INTEGRITY_MURMUR_HASH says its going to do - the indirection is required to
    //  allow propogation / multiple use of the __COUNTER__ value.
    #define INSERT_INTEGRITY_MURMUR_HASH(IVID, SEQUENCE_ID, SEEDING, KNOWN_VALUE, ...)       \
        ANNOTATE_HASH_PATCH__INSERT_MURMUR(IVID, SEQUENCE_ID, SEEDING, KNOWN_VALUE) \
        INSERT_MARKED_CODE_REGION(IVID, __VA_ARGS__)



    /// MurmurOOAT64 method (ish) - calculates the hash of the given data buffer.
    //  @param data_buffer a pointer to the data to caclulate a hash of.
    //  @param length the amount of data to hash from @p data_buffer.
    //  @param state the current state of the hash, or if the first buffer hashed can be used as a seed value.
    //  @returns the state of the hash after the given data buffer has been consumed - either use or feed back in as state.
    unsigned long murmur_oaat64(const unsigned char * data_buffer, unsigned long length, unsigned long state);

    /// Calculates a hash of this binaries "predictable" contents.
    //  @param state the state (or seed) used to initialise the hashing algorithm.
    //  @param memory_pool the memory pool to use to allocate dynamic memory.
    //  @returns the hash of the fixed content of the binary.
    unsigned long calculate_binary_hash(unsigned long state, MemoryPool* memory_pool);

#endif