#include "twister.h"


/// The size of a word in bits
//  @remarks could consider using 64 in future - see MT19937-64 on wikipedia.
//     to relevant parameters - would also need to change internal data types.
#define WORD_SIZE           (32)

/// Masks to ensure generated values fit in word size.
//  Operates with long values (8 bytes in context), this is used to discard overflow.
#define WORD_MASK           ((1UL << WORD_SIZE) - 1)

/// The most signficant bit of the word.
#define BITMASK_32B_MSB     (1UL << (WORD_SIZE - 1))

/// All the other bits of the word
#define BITMASK_32B_317LSB  ( ~BITMASK_32B_MSB )



/// MT19937 'a' component
//  Coefficients of the rational normal form twist matrix
#define MT19937_A (0x9908B0DF)

/// MT19937 'b' component
//  TGFSR(R) tempering bitmasks
#define MT19937_B (0x9d2c5680)

/// MT19937 'c' component
//  TGFSR(R) tempering bitmasks
#define MT19937_C (0xefc60000)

/// MT19937 'f' component
//  The constant f forms another parameter to the generator, though not part of the algorithm proper.
//  @remarks The value for f for MT19937 is 1812433253
#define MT19937_F (0x6C078965)

/// MT19937 'l' component
// Additional Mersenne Twister tempering bit shifts/masks
#define MT19937_L (0x00000012)

/// MT19937 'm' component
//  Middle word, an offset used in the recurrence relation defining the series: x, 1 <= m < n
#define MT19937_M (0x0000018d)

/// MT19937 's' component
//  TGFSR(R) tempering bit shifts
#define MT19937_S (0x00000007)

/// MT19937 't' component
//  TGFSR(R) tempering bit shifts
#define MT19937_T (0x0000000f)

/// MT19937 'u' component
//  Additional Mersenne Twister tempering bit shifts/masks
#define MT19937_U (0x0000000b)



/// Creates a new PRNG state initialised from the given seed.
//  @param seed the seed value to use to initialise the PRNG state.
//  @returns a new PRNG state that can be used to generate random numbers.
MersenneTwister create_mersenne_twister(unsigned int seed) {

  MersenneTwister mersenne_twister;

  mersenne_twister.state[0] = seed;

  for(mersenne_twister.index=1; mersenne_twister.index < MT19937_STATE_SIZE; mersenne_twister.index++) {
    unsigned int v = mersenne_twister.state[mersenne_twister.index-1];
    mersenne_twister.state[mersenne_twister.index] = (MT19937_F * (
        v ^ (v >> (WORD_SIZE - 2))
    ) + mersenne_twister.index) & WORD_MASK;
  }

  return mersenne_twister;

}

/// Creates a new PRNG state initialised from the given long seed.
//  NOTE: the long does not add additional entropy - this is just a way of seeding
//    with a long rather than a integer.
//  @param seed the seed value to use to initialise the PRNG state.
//  @returns a new PRNG state that can be used to generate random numbers.
MersenneTwister create_mersenne_twister_long(unsigned long seed)
{
  unsigned int lhs = (unsigned int)((seed & 0xffffffff00000000) >> 32);
  unsigned int rhs = (unsigned int)((seed & 0x00000000ffffffff) >> 0);
  return create_mersenne_twister(lhs ^ rhs);
}


/// "Twist" internal state
//  Progresses the internal state when all current values have been consumed.
//  @param mersenne_twister the PRNG to advance the state of.
void _twist(MersenneTwister* mersenne_twister)
{  
    for(unsigned int index=0; index < MT19937_STATE_SIZE; index++) 
    {
        unsigned int next_index = (index + 1) % MT19937_STATE_SIZE;
        unsigned int take_index = (index + MT19937_M) % MT19937_STATE_SIZE;
        
        unsigned long x = (mersenne_twister->state[index] & BITMASK_32B_MSB) | 
                (mersenne_twister->state[next_index] & BITMASK_32B_317LSB);

        unsigned long xA = x >> 1;
        
        mersenne_twister->state[index] = mersenne_twister->state[take_index] ^ ((x % 2) ? xA ^ MT19937_A : xA);
    }

    mersenne_twister->index = 0;
}


/// Generates the next unsigned 32bit number in the PRNGs sequence.
//  @param mersenne_twister the state to use to generate the next number.
//  @returns the next number from the PRNG's random sequence.
unsigned int next_mersenne_twister_uint32(MersenneTwister* mersenne_twister) 
{
  if(mersenne_twister->index >= MT19937_STATE_SIZE) 
    _twist(mersenne_twister);

  unsigned int y = mersenne_twister->state[mersenne_twister->index++];
  y ^= (y >> MT19937_U) & WORD_MASK;
  y ^= (y << MT19937_S) & MT19937_B;
  y ^= (y << MT19937_T) & MT19937_C;
  y ^= (y >> MT19937_L);
  
  return y & WORD_MASK;

}