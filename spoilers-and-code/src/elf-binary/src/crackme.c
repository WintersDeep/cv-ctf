#include "protected-string.h"
#include "common.h"
#include "memory.h"
#include "integrity.h"
#include "twister.h"

#define PRIMARY_INTEGRITY_CHAIN "primary"
#define IC_GATE_0 (10)
#define IC_GATE_1 (IC_GATE_0 + 10)
#define IC_GATE_2 (IC_GATE_1 + 10)
#define IC_GATE_3 (IC_GATE_2 + 10)
#define IC_GATE_4 (IC_GATE_3 + 10)
#define IC_GATE_5 (IC_GATE_4 + 10)

#define PASSWORD_PROMPT_STR     "Password: "
#define BAD_PASSWORD_STR        "Sorry, thats not it.\n"
#define GOOD_PASSWORD_STR       "OK - Flag: "
#define DEBUGGER_PASSWORD_STR   "No debugging me!"

#ifndef PASSWORD_MT_SEED_QWORD // goodbury
#define PASSWORD_MT_SEED_QWORD 0x79727562646f6f67
// 0xf5, 0xc9, 0x29, 0x51, 0x02, 0x00, 0x3a, 0xa2, 0x63, 0x41, 0x53, 0xc8, 0xd0, 0xb2, 0x58, 0xa2, 0x66, 0xbe, 0x0e, 0x0c
#pragma message("PASSWORD_MT_SEED_QWORD was not defined - using default value - you'd want to use a real value for release.")
#endif

#ifndef PASSWORD_MASK_STRING // xor mask for default PASSWORD_MT_SEED_QWORD resulting in "wintersdeep\0"
#define PASSWORD_MASK_STRING "\x82\xa0\x47\x25\x67\x72\x49\xc6\x06\x24\x23\xc8"
#pragma message("PASSWORD_MASK_STRING was not defined - using default value - you'd want to use a real value for release.")
#endif

#ifndef FLAG_RAW_VALUE // the actual final flag value.
#define FLAG_RAW_VALUE "TESTFLAG" 
#pragma message("FLAG_RAW_VALUE was not defined - using default value - you'd want to use a real value for release.")
#endif

#ifndef FLAG_MT_SEED_QWORD // 1925-2-3 (With sufficient thrust, pigs fly just fine).
#define FLAG_MT_SEED_QWORD 0x332d322d35323931
#pragma message("FLAG_MT_SEED_QWORD was not defined - using default value - you'd want to use a real value for release.")
#endif

#ifndef FLAG_MASK_STRING // xor mask for default FLAG_MT_SEED_QWORD resulting in FLAG_RAW_VALUE with a tailing NUL.
#define FLAG_MASK_STRING "\x4e\x0a\xf6\xf9\x49\x35\xb5\x38\x4b"
#pragma message("FLAG_MASK_STRING was not defined - using default value - you'd want to use a real value for release.")
#endif

typedef struct crackme_state_
{
  unsigned long integrity_hash;

  MemoryPool memory_pool;

} crackme_state;



unsigned char next_password_character(unsigned int index, MersenneTwister* mt, unsigned int *current_mt_value, char* buffer, unsigned int buffer_size)
{
    if(index % 4 == 0)
    {
        *current_mt_value = next_mersenne_twister_uint32(mt);
    } 
    const unsigned char mt_char = ((char*)current_mt_value)[index % 4];
    const unsigned char buffer_char = buffer[index % buffer_size];
    unsigned char tmp = buffer_char ^ mt_char;
    return tmp;
}

unsigned long check_password(char* password_string, unsigned int password_size, crackme_state* state)
{
    unsigned long result = 0;
    char* buffer = allocate_memory(&state->memory_pool, POOL_PAGE_SIZE);

    if(buffer)
    {
        MersenneTwister mt;
            
        REQUIRES_INTEGRITY_XOR_TO_KNOWN(PRIMARY_INTEGRITY_CHAIN, IC_GATE_1, PASSWORD_MT_SEED_QWORD, {
            unsigned long seed = state->integrity_hash ^ XOR_MASK_FOR_KNOWN_VALUE;
            mt = create_mersenne_twister_long(seed);
        })

        CONTAINS_INTEGRITY_HASH(PRIMARY_INTEGRITY_CHAIN, IC_GATE_2, {
            state->integrity_hash = calculate_binary_hash(state->integrity_hash, &state->memory_pool);
        })

        ASSIGN_PROTECTED_STRING(buffer, PASSWORD_MASK_STRING);

        unsigned int i = 0;
        unsigned int current_mt_value = 0;

        // this loop checks the password one character at a time - it never holds the full string decrypted.
        // each character is XOR'd against the correct value in memory and deviation is recorded. 
        for(; i < password_size; i++)
            result += next_password_character(
                i, &mt, &current_mt_value, buffer, sizeof(PASSWORD_MASK_STRING)
            ) ^ password_string[i];

        CONTAINS_INTEGRITY_HASH(PRIMARY_INTEGRITY_CHAIN, IC_GATE_3, {
            state->integrity_hash = calculate_binary_hash(state->integrity_hash, &state->memory_pool);
        })

        // ensure this is the end of the string, otherwise you can short the check by entering part (or nothing).
        if(next_password_character(
                i, &mt, &current_mt_value, buffer, sizeof(PASSWORD_MASK_STRING)
        ) != 0x00) result += 1;

        release_memory(&state->memory_pool, buffer);
    }

    return result;
}

void release_flag(crackme_state* state)
{
    // allocate a buffer to store our response (output)
    char* buffer = allocate_memory(&state->memory_pool, POOL_PAGE_SIZE);

    if(buffer)
    {

        MersenneTwister mt;

        // increment integrity hash.
        CONTAINS_INTEGRITY_HASH(PRIMARY_INTEGRITY_CHAIN, IC_GATE_4, {
            state->integrity_hash = calculate_binary_hash(state->integrity_hash, &state->memory_pool);
        })

        // create a mersenee twister with a known seed from integrity.
        REQUIRES_INTEGRITY_XOR_TO_KNOWN(PRIMARY_INTEGRITY_CHAIN, IC_GATE_4, FLAG_MT_SEED_QWORD, {
            unsigned long seed = state->integrity_hash ^ XOR_MASK_FOR_KNOWN_VALUE;
            mt = create_mersenne_twister_long(seed);
        })

        // unpack the "here is the password" prefix into the output buffer.
        ASSIGN_PROTECTED_STRING(buffer, GOOD_PASSWORD_STR);
        char *flag_string = buffer + sizeof(GOOD_PASSWORD_STR);

        // unpack half the hidden flag XOR mark into the remainder of the output buffer.
        ASSIGN_PROTECTED_STRING(flag_string, FLAG_MASK_STRING);

        unsigned int i = 0;
        unsigned int current_mt_value = 0;
    
        do
        {   // user the mersenne twister sequence as the second XOR source to "decrypt" the flag.
            flag_string[i] = next_password_character(i, &mt, &current_mt_value, flag_string, sizeof(FLAG_MASK_STRING));
        } while(i < POOL_PAGE_SIZE && flag_string[i++] != 0x00);


        // increment integrity hash.
        CONTAINS_INTEGRITY_HASH(PRIMARY_INTEGRITY_CHAIN, IC_GATE_5, {
            state->integrity_hash = calculate_binary_hash(state->integrity_hash, &state->memory_pool);
        })

        REQUIRES_INTEGRITY_MURMUR_HASH(PRIMARY_INTEGRITY_CHAIN, IC_GATE_5, FLAG_RAW_VALUE, {

            // check that the flag we decrypted is correct - it may be wrong if the integrity 
            // machanism has been botched to bypass the password (it'll cause the wrong seed to be
            // passed to the mersenne twister resulting in garbage in the output buffer).
            if (murmur_oaat64(flag_string, i - 1, state->integrity_hash) == EXPECTED_MURMUR_HASH)
            {
                // all goood - increment output size by size of prefix.
                i += sizeof(GOOD_PASSWORD_STR);
            }
            else
            {
                // the flag is nonsense (at least it doesn't match what we expected) - the user 
                // corrupted state at some point so was obviously debugging, scold them appropriately.
                i = sizeof(DEBUGGER_PASSWORD_STR);
                ASSIGN_PROTECTED_STRING(buffer, DEBUGGER_PASSWORD_STR);
            }

            buffer[i++] = '\n';
            stdout(buffer, i);
        })

    }

}

void _start(void)
{
    crackme_state state = {
        .memory_pool = create_memory_pool()
    };
    
    if(state.memory_pool.base_address)
    {
        CONTAINS_INTEGRITY_HASH(PRIMARY_INTEGRITY_CHAIN, IC_GATE_0, {
            state.integrity_hash = calculate_binary_hash(INTEGRITY_SEED, &state.memory_pool);
        })

        char* buffer = allocate_memory(&state.memory_pool, POOL_PAGE_SIZE);
        
        if(buffer) 
        {
            char bytes_read;

            ASSIGN_PROTECTED_STRING(buffer, PASSWORD_PROMPT_STR);
            if(stdout(buffer, sizeof(PASSWORD_PROMPT_STR)) == 0)
            {
                CONTAINS_INTEGRITY_HASH(PRIMARY_INTEGRITY_CHAIN, IC_GATE_1, {
                    state.integrity_hash = calculate_binary_hash(state.integrity_hash, &state.memory_pool);
                    bytes_read = readline_stdin(buffer, POOL_PAGE_SIZE-1);
                })

                if(bytes_read)
                {
                    if( check_password(buffer, bytes_read, &state) == 0 )
                    {
                        release_flag( &state );
                    }
                    else
                    {
                        ASSIGN_PROTECTED_STRING(buffer, BAD_PASSWORD_STR);
                        stdout(buffer, sizeof(BAD_PASSWORD_STR));
                    }
                }                
            }

            release_memory(&state.memory_pool, buffer);
        }


        
        

        destroy_memory_pool(&state.memory_pool);
        sys_exit(0);

        // asm volatile(
        //     "dec %eax;"
        //     "mov -8(%ebp),%ebx;"
        //     "leave;"
        //     "retf;"
        // );

    }

}