# Flag #4: The only problem is I forgot to note down the password

This flag is embedded in an ELF executable which wants a password. Given the correct password the binary will yield the flag. Unfortunatly, so the hook goes, I "forgot" the password.

This one I personally consider the hardest flag, and its also the only one I'm not giving answers for (other than the fact that all the source and build tools are provided, and I'm going to tell you exactly how it works). It's my way of making sure there isn't a complete answer sheet and I know anyone able to give the last flag has done some leg work. The hints here however will make accessing the password easier, esp. if your familiar with some assembly and modern debugging tools.

## Polymorphic Build Process

Various aspects of the code are generated randomly at build-time. Whilst this does make production of an automated solver for this more difficult (or at least a future proof one), it was actually implemented for two other reasons:

- As a string obfuscation technique (see [how strings are protected](#protected-strings)).
- To be a demonstration of a technique malware might use to avoid byte sequence fingerprinting.
- Because I thought it was a neat property to have.

## Corrupted ELF Header

The binary has a non-standard ELF header. This can break some debuggers, but does not prevent the ELF from running natively. The headers biggest "fraud" is that it claims to use big-endian encoding; the `EI_DATA` field of the `e_ident` structure is set to  `ELFDATA2MSB` (`0x02`).

The native loader does not look at this value, it doesn't need to, there is no such thing as x86 big-endian - its just assuming its CPU compatible anyhow. However debuggers and disassemblers are designed to work with a variety of target platforms. They will see this and try to honour it; funnily enough if you start decoding values with the wrong endian you get some wildly inappropriate values and funny results.

## What architecture are you again?

The binary claims to be, an nominally is, an 32-bit binary. However, thats not really the full story. The whole purpose of the 32-bit code is to unpack the real binary, which is compiled in 64-bit. After it has unpacked this code, it changes the CPU to long mode and hands off to the unpacked content. 

This results in a 32-bit process that is executing 64-bit instructions. An important distinction here - this action does not change the nature of the parent process, only the type of instructions that it is executing. This can have interesting side-effects that might catch you off-gaurd (for example trying to use `mmap` via a 64-bit `syscall` will likely fail unless passed the `MAP_32BIT` flag when running in a 32-bit process) - I was intending on using this for deceptive logic (a `mmap` call I knew would fail, so people following along in disassemblers - rather than debuggers - might follow the wrong branch).

It can also have some interesting impacts to debugging; historically this made the process very hard to debug - 64-bit debuggers refused to attach to a 32-bit process, whilst a 32-bit debugger would choke once the instruction set changed, either crashing outright or reporting the wrong instructions. It could even messed with `strace` resulting in it printing garbage. Some debuggers now offer a way to change instruction set at runtime, but this is not always the case. Even where it is available it can be buggy and usually requires an operator to tell it to change.

## FizzBuzz (ish)

During an interview in the way back. after answering a question about stack smashing I was asked to code fizz-buzz. It was an interesting change of vector. I decided to prempt this next time by implementing it into the unpacker for the 64-bit code. 

The 64-bit code is XOR encoded against a byte key (wrapping at `0xff`) that is initialised to 1 and incremended by:

- `FIZZ` if the byte index is a mulitple of `FIZZ_UP`.
- `BUZZ` if the byte index is a mulitple of `BUZZ_UP`.
- `FIZZ + BUZZ` if the byte index is a multiple of both `FIZZ_UP` and `BUZZ_UP`.
- By `1` if the byte index is none of the above.

The specific values for `FIZZ`, `BUZZ`, `FIZZ_UP`, and `BUZZ_UP` are randomly generated per build.

## Memory Integrity

Once you enter the 64-bit code the program periodically calculates a checksum of the entire 64-bit code memory region, excl. one or two specific offsets (DWORD values that relate to this checksum and cannot be calculated ahead of time) - this checksum is salted. The first "check" is salted with a random per-build value, with each successive check being salted with the output of the previous one. 

This means any patching of the software will break this checksum value - this could even be incidental such as by placing software breakpoints which replace the first byte of the specified program instruction with an debugger instruction such as `int3` (`0xcc`), `into` (`0xce`), or `int1` (`0xf1`). It is for this reason that at some point it will be almost essential you use a tool that supports hardware breakpoints for this CTF.

This checksum is used in the protection of sensitive strings (see [sensitive strings](#sensitive-protected-strings)). If the checksum value is incorrect, these strings will fundementally fail to decode properly. It is unlikely the software will tell you that you broke this integrity mechanism (the password check will just fail as if you gave it the wrong password), although there is one specific situation where this is disclosed.

## Protected Strings

If you search for strings in the binary you will come up blank, there is no data section and no raw characters embedded in the binary (unless you count `ELF` in the ELF header structure I guess); this is by design, and is designed to be annoying.

There are two types of strings in this crackme - _"protected strings"_, and _"sensitive strings"_. 

- _"Protected strings"_ are trivial things we don't really mind disclosing (messages to the user mostly), they are protected to avoid making it easy to see what a peiece of logic does. That is to say you will probably easily recognise a string is being "built", but not immediately what it says - this makes pre-emptive placement of breakpoints on interesting code a little harder.
- Sensitive strings are the things we _really_ want to protect, the flag and password. They are an extension of "protected strings" which integrates the ["memory integrity"](#memory-integrity) mechanism we discussed previously. 

Protected strings are built in memory when they are needed - they exist nowhere in the program at rest. The specific instructions used to build the strings are randomly generated per-build by selecting a chain of _"gadgets"_ to assemble the required characters. 

- Each gadget defines a specific quantity of characters it will assemble.
- The order that characters are assigned into the string is entirely random.
- Some gadgets fill zero characters - these are considered "junk" gadgets and implement behaviours to obfuscate the decoding process.
- Most assignment gadgets (gadgets that actually build the strings) currently operate on XOR operations. They will prefer taking their operands from existing bytes in the software (i.e. to compose the letter `A` a gadget might try to find two bytes in the program text that XOR to this value). Sometimes this isn't possible, in such cases one of two things happen:
    - The _"junk_" gadgets previously discussed can inject bytes into the software that have no specifically required value (they are literally garbage), these bytes values can be assigned to supply a missing XOR operand if required.
    - If there are no available junk bytes to fill the XOR operand (no junk gadgets used, or no junk bytes available/inserted) a literal value to complete the XOR pair may be used.

This process has a few "benefits":

- It makes it very difficult to extract strings - there is no encoded block you can just dump and decode. The only way to decode the strings is to run (or emulate) the code, and each strings decode is unique.
- As the strings are infused into the whole program text, you can only really process them by taking the whole binary (you can't just isolate the relvant data very easily).
- Altering the program (even by software breakpoint) no longer just runs the risk of breaking the [memory integrity](#memory-integrity) mechanism; you might also break the strings in the binary (note it is entirely possible that a byte in code used to decode one string is used as an XOR component whilst decoding another one).
- Its often easier to just place a break point at the end of a strings decoding process to see what comes out, but this leads you into a risk of placing a software breakpoint and running afoul of the integrity checking mechanism, or me deciding to randomly bury some very important business logic in the middle of that process.
- No two builds are the same. Its very hard to tell if a string changed between builds because the instructions are variable as are the memory components that they use.

However this is fairly easy to side-setp with hardware breakpoints. It just helps protect using strings to isolate program logic.

## Sensitive Strings

Sensitive strings protect secrets; the flag and password. They build off the  [memory integrity](#memory-integrity) and [protected strings](#protected-strings) systems. So you'll want to understand those first.

Sensitive strings are basically built by combining the two.

1. The protected string system is used to protect a binary sequence rather than an ASCII string.
1. The current memory integrity checksum is used to seed a random number generator (merseene twister).
1. Each byte in the binary sequence is XOR'd against the output of the random number generator until a NUL byte is encountered. The result is the protected secret.

This is useful because anyone could theoretically decode the binary sequence, but it is meaningless without also knowing the correct PRNG seed. This is a weak cryptographic key, and one statergy might be to manually decode the XOR sequence and then brute forcing the PRNG seed (although I would note; the PRNG implementation might not be strictly to the book so YMMV if you don't faithfully reimplement the PRNG implementation). Brute forcing isn't even really required, you just need to know the hash initialisation value and how many times to iterate the hash algorithm to land on the correct seed value.

When checking the password each byte is checked independently as its XOR decoded (meaning a single decoded character is held in memory at any time). If you ever tampered with memory and this corrupted the memory integrity hash - the random number generator is going to generate the wrong seqeunce and the XOR decode is going to be wild (in most cases the resulting "password" isn't even typeable).

It is possible, given the nature of random numbers, that with broken integrity seed. you still generate a sequence that is typeable, and maybe you use the debugger to step over the password check (or you just get lucky and happened to enter that exact "wrong" password - consider buying a lottery ticket). In this specific case the password will be accepted. However, when the flag string is decoded the same method is used "sensitive string" protection mechanism is used and will generate the wrong flag. To protect against the software emitting this (as if it were the correct flag, thus possibly causing confusion) the flag is first ran through the same hashing method used for memory integrity checking (using the current integrity hash as salt), this is compared against the flags known hash. It is astronimally improbable this hash will match the generated password given the wrong seed values, and in this very specific case the binary will tell you that you broke integrity, and that the flag it generated is not valid.

# The framework of a solution

As stated elsewhere, I'm not giving an explicit answer to solving this flag - however below I have included the most direct path to cracking this binary as "broad-stroke" steps. Its hidden in case you'd like to try it yourself.

<details>
<summary><strong>Solution framework</strong></summary>

The following is a suggestion for how you might go about solving this crackme.

1. If your debugger can't handle the mangled ELF header fix it (set the data class to little endian).
1. If your debugger can't handle changes to instruction set at run time, consider dumping the 64-bit code. Its position independent and uses no libraries by design (its practically floating shellcode); it can be easily dumped to a file and an 64-bit ELF header slapped on it. This might be useful even if your debugger can handle the transition to avoid having to worry about effects in the unpacking process (unpredictable memory location of the 64-bit code for example).
1. Debug the software and work out where the password check is performed. Don't worry about breaking integrity at this point. Use software breakpoints if you want. Decode all the strings. Just find the password check.
1. Once you've done this set a hardware breakpoint at that location, clear all previous breakpoints, and restart the process. 
1. Enter any gargbage password (of reasonable length), and dump each character of the legitimate password as its checked.
1. Finally, armed with the legitimate password restart the software without the debugger and claim the flag.

</details>


## Considerations / Other Ideas / Suggestions

- This could be considered a quite technically involved binary and utilises technique more commonly seen in malware to defend itself.
- I've tried to pick interesting, but approachable protection techniques over more robust, traditional or frustrating ones.
- The route to extracting the password is pretty direct once you know what is happening. This is by design, most people in reciept of this CTF are not going to be having much time to engage with it so I want it to be accessible (without feedback I dont/wont know if I achieved this objective). 
- The following idea's were considered but have not been implemented by choice:
    - Any technique that immediately boots the analyst (calling `exit` or crashing prematurely if they are noticed). This is just going to get frustrating when trying to reason with the code.
    - In a similar vein to the above, excessive use of primitives designed to be "dead-ends" (branches of logic that run into the hills and frolic, but do nothing meaningful - esp. in response to an analyst being detected)
    - Techniques to detect the debugger itself (i.e. testing if a debugger is attached, testing if vast amounts of real-world time have elapsed between markers we'd typically expect to bridged in milliseconds, etc). We already have the memory integrity - which is designed to make debugging harder, not prevent debugging, and the idea here isn't to make actual malware or DRM.
    - Additional techniques to prevent debuggers attaching (such as getting the software to `fork` and debug itself), we already do a long mode transition - its interesting and enough in this context.
    - Dropping in/out of long mode repeatedly making it hard to get a view of the entire code base.
    - Using multiple components ancommunicating over IPC to setup interdependency.
- It would be interesting to embed a payload in a custom bytecode/IL, but this would be far to excessive for this I feel for the target audience and timeframe of this CTF.