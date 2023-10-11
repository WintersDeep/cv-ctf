#ifndef CVCTF_TWISTER_H
#define CVCTF_TWISTER_H

// = Mersenne Twister PRNG
//
// Simple PRNG used for predictable random number generation. We could have relied on an open 
// source implementation but they usually come with features we don't need and may use 
// alternate seeding mechanics - we need to be able to reproduce values created by this 
// generator in the patching tool, so it helps to be in full control of things.
//
// Base on; [Wikipedia's documentation for MT19937](https://en.wikipedia.org/wiki/Mersenne_Twister)
//
// For more information see the documentation.


/// The size of the internal PRNG's state 
//  "n: degree of recurrence" in documentation.
#define MT19937_STATE_SIZE  624


/// Mersenne twister PRNG state
typedef struct _MersenneTwister {

  /// Internal state
  signed long state[MT19937_STATE_SIZE];

  /// Offset/index into state.
  signed int index;

} MersenneTwister;


/// Creates a new PRNG state initialised from the given seed.
//  @param seed the seed value to use to initialise the PRNG state.
//  @returns a new PRNG state that can be used to generate random numbers.
MersenneTwister create_mersenne_twister(unsigned int seed);


/// Creates a new PRNG state initialised from the given long seed.
//  NOTE: the long does not add additional entropy - this is just a way of seeding
//    with a long rather than a integer.
//  @param seed the seed value to use to initialise the PRNG state.
//  @returns a new PRNG state that can be used to generate random numbers.
MersenneTwister create_mersenne_twister_long(unsigned long seed);


/// Generates the next unsigned 32bit number in the PRNGs sequence.
//  @param mersenne_twister the state to use to generate the next number.
//  @returns the next number from the PRNG's random sequence.
unsigned int next_mersenne_twister_uint32(MersenneTwister* mersenne_twister);


#endif // CVCTF_TWISTER_H