// = Protected Strings (`PROTECTED_STRING`)
//
// Protected strings are character strings we want to embed in the binary, but not be trivially readable.
// Rather than a direct string assignment these strings are "built". This is done by assigning the string 
// value character by character; the specific mechanics of how each character is assigned are randomly 
// determined by a post-build step.
//
// This preprocessor will:-
//   - Determine how many bytes of ASM code it will take to perform the assignment.
//   - Reserve an appropriate number of bytes to achieve the character-by-character assignment in the 
//       appropriate memory location use NOP instructions.
//   - Store the string to be assigned, and the location of where it needs to be built in an ELF section.
//
// The actual code responsible for doing this is injected by a post-build tool. This is done for a 
// variety of reasons; for example:-
//   - It allows us to use values from the build environment (such as bytes that exist in the binary).
//   - It allows us to create random steps so each build is unique.
//
// For more information see the documentation.

#ifndef CVCTF_STRINGS_H
#define CVCTF_STRINGS_H

// If `WNOPROTECTED_STRINGS` is defined we disable protected strings - this will replace the above 
// described behaviour with a simple `strcpy()` of the intended value instead.
#ifndef WNOPROTECTED_STRINGS

    /// Calculates the length of a string.
    #define STRLEN(STR) (sizeof(STR) )


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

    /// Structure of a protected string section entry.
    ///
    /// This structure defines the information that we capture about protected strings. Its used
    /// by the post-build step to determine where and what needs fixing up.
    struct protected_string_section_entry
    {
        /// The VMA where bytes have been reserved to build a string.
        void*           reservation_virtual_memory_address;

        /// The number of bytes that has been reserved build the string.
        ///
        /// Note; that this is calculatable by the the post-build step tooling and is mostly
        /// included as a sanity check.
        unsigned int    reservation_size;

        /// The string that we wanted to be built at this location.
        char            expected_string[];
    };

    /// The number of bytes to reserve as general overhead for building a protected string.
    ///
    /// See `PROTECTED_STRING_RESERVE_SIZE` for more information.
    #define PROTECTED_STRING_RESERVE_OVERHEAD 0x10

    /// The number of bytes to reserve as per-character when building a protected string.
    ///
    /// See `PROTECTED_STRING_RESERVE_SIZE` for more information.
    #define PROTECTED_STRING_RESERVE_PER_CHAR 0xf

    /// Calculates the number of bytes we need to reserve to build the specified string `STR`
    ///
    /// To calculate how many bytes to reserve the pre-processor basically does an `O + (N * string_length)`
    /// calculation; where `O` is a fixed-size _"overhead"_ value and `N` is a fixed multiplier per character in the string.
    #define PROTECTED_STRING_RESERVE_SIZE(STR) (STRLEN(STR) * PROTECTED_STRING_RESERVE_PER_CHAR) + PROTECTED_STRING_RESERVE_OVERHEAD

    /// Determines the label string for the given protected string ID `PSID`.
    #define PROTECTED_STRING_ANNOTATION_NAME(PSID) PROTECTED_STRING_ ## PSID

    /// The prefix used for sections that record the location of protected strings
    ///
    /// The post-build tool will look for this prefix to determine what work it needs to do when patching the binary.
    #define PROTECTED_STRING_ANNOTATION_PREFIX ".protected-string-entry"

    /// Creates a protected string annotation.
    ///
    /// This is doint some lifting for us; it creates a section which records the location that this macro is called. It does this
    /// by using the provided `PSID` to create a unique label at the current location. It uses this label along with the [GCC's 
    /// "label-as-value" mechanic](https://gcc.gnu.org/onlinedocs/gcc-3.2.3/gcc/Labels-as-Values.html) to locate itself. 
    ///
    /// @note; the semi-colon after the label is important - its not an oversight. GCC doesn't allow labels in some locations; the
    ///   semi colon below creates an empty statement that GCC is always happy allow to be labelled.
    #define ANNOTATE_PROTECTED_STRING(PSID, STR)                                                                                \
        {                                                                                                                       \
            static __attribute__( ( section(PROTECTED_STRING_ANNOTATION_PREFIX "." __FILE__ ":"  INDIRECT(__LINE__)) ) )        \
                struct protected_string_section_entry _ = {                                                                     \
                    .reservation_virtual_memory_address = &&PROTECTED_STRING_ANNOTATION_NAME(PSID),                             \
                    .reservation_size                   = PROTECTED_STRING_RESERVE_SIZE(STR),                                   \
                    .expected_string                    = STR                                                                   \
                };                                                                                                              \
            PROTECTED_STRING_ANNOTATION_NAME(PSID): ; /* do not remove semi-colon; see comment above */                         \
        }                                                                                                                       \

    /// Reserves space for assigning the specified `STR` into the memory pointed at by `VARNAME`.
    ///
    /// Uses inline ASM to achieve two things - it _"reserves"_ an appropriate amount of code space to inject the ASM later that
    /// will build the string. This is done by a post-build step. This is done using the `.fill` macro to inject an appropriate
    /// amount of NOP instructions. It also guarentee's that RBX points to the location in memory that we intend to create the 
    /// string at, and informs the compiler that memory might have been altered.
    ///
    /// @note the `volatile` keyword is important - we do not want GCC compiling this out as it will look useless before we
    ///   patch it in the post-build step.
    #define RESERVE_TEXT_SPACE_FOR_PROTECTED_STRING(VARNAME, STR)               \
        {                                                                       \
            asm volatile (                                                      \
                ".fill %c[reserve_size], 1, 0x90"                               \
                :                                                               \
                : [reserve_size] "i" (PROTECTED_STRING_RESERVE_SIZE(STR)),     \
                                  "b" (VARNAME)                                 \
                : "memory", "cc", "rax", "rcx", "rdx"                           \
                                                                                \
            );                                                                  \
        }                                                                       

    /// Indicates that the string value `STR` should be assigned to the memory pointed to by `VARNAME`
    ///
    /// Annotates the location and reserves space for the post-build step to assign the given string.
    /// 
    /// @note This does not assign the string in any way now - if the post-build step is not ran and this
    ///    binary remains unpatched the memory pointed to by `VARNAME` remains unaltered. This could result
    ///    in undefined behaviour.
    #define ASSIGN_PROTECTED_STRING(VARNAME, STR)                               \
        ANNOTATE_PROTECTED_STRING(__COUNTER__,STR)                              \
        RESERVE_TEXT_SPACE_FOR_PROTECTED_STRING(VARNAME, STR)


#else // WNOPROTECTED_STRINGS was specified

    /// Indicates that the string value `STR` should be assigned to the memory pointed to by `VARNAME`
    ///
    /// (WNOPROTECTED_STRINGS) - uses a basic strcpy to implement this behaviour now.
    #define ASSIGN_PROTECTED_STRING(VARNAME, STR)                                       \
        strcpy(VARNAME, STR);

#endif


/// Creates a heap-allocated `char*` with the given `VARNAME` assigned the given `STR` value using the ASSIGN_PROTECTED_STRING mechanic.
///
/// Because I am lazy and this is usually the context in which this will be used.
#define ALLOC_PROTECTED_STRING(VARNAME, STR)                                            \
    char* VARNAME = malloc( STRLEN(STR) );                                              \
    ASSIGN_PROTECTED_STRING(VARNAME, STR)

#endif // CVCTF_STRINGS_H