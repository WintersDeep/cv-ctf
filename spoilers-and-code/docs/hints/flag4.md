# Flag #4: The only problem is I forgot to note down the password

This document contains hints for the fourth flag. 

Its here to give some extra nudges if your trying to complete the CTF yourself but get a little lost or stuck.

> **NOTE** Unlike previous hints these are a little more direct. I'm going on the assumption that subtle might not be enough here if you need hints.

---

<details>
<summary><strong>Troubleshooting: I run the binary and nothing happens</strong></summary>

This may well be _"expected behaviour"_ for your computer. Run the following command:

```bash
./crackme; echo "${?}"
```

This should output the programs _"exit code"_. If the output indicates the exit code is `255` the program is behaving as expected. Consider trying to work out why the binary is doing this. 

Remember, the binary will lie to you and may not be what it appears to be.

<details>
<summary><strong>Just tell me how to fix it...</strong></summary>

You are running the program on an 32-bit operating system.

Unfortunatly the binary requires a 64-bit operating system.

Move it over to one and you should find it starts behaving.

</details>
</details>

---

<details>
<summary><strong>Troubleshooting: My tools tell me the binary is corrupted / not an executable.</strong></summary>

The binary will lie to you and your tools; run it on the command line - if you see a `Password: ` prompt then the binary is exactly as its meant to be. 

If your stuck, start unwrapping hints.

</details>

---

<details>
<summary><strong>Hint 1/4</strong></summary>

The binary will lie to you, it may not be what it claims to be. This may break your tools.

<details>
<summary><strong>Be explicit - what does this mean?</strong></summary>

The binaries PE header is a little malformed and may need to be altered for some tools to load the file. These changes do not intefer with the native ELF loader.

</details>

---

<details>
<summary><strong>Hint 2/4</strong></summary>

The nature of some things change; these changes can break some tools, or make them speak in tongues.

<details>
<summary><strong>Be explicit - what does this mean?</strong></summary>

The binary claims to be, and nominally is, a 32-bit binary. However it changes the CPU mode to 64-bit during execution. Its important to keep in mind the binary is still running as a 32-bit process; its just that now the 32-bit process is executing 64-bit instructions. 

This can break some tools as a 64-bit debugger might not want to attach to a 32-bit process, and a 32-bit debugger will get confused by the 64-bit instructions. 

How you handle this will depend on your toolset. Modern tools may allow you to swap instruction set at runtime. Otherwise you might consider isolating the 64-bit code into its own binary (the 64-bit elements are the core logic and have been specifically made as a single and standalone blob for this purpose).
</details>

---

<details>
<summary><strong>Hint 3/4</strong></summary>

Be careful that the observer does not alter the observed. You too are being watched.

<details>
<summary><strong>Be explicit - what does this mean?</strong></summary>

Once you've transitioned to 64-bit code the binary periodically performs an integrity check of its own virtual memory. If the 64-bit code has been altered you may break this integrity mechanism (note that the way this is done may mean you are not immediately made aware that you've been rumbled if it ever tells you at all, it may just refuse the correct password). Note that in context, altering the 64-bit code doesn't just mean patching instructions to alter behaviour - consider how some types of breakpoint work and how that might impact an integrity check of virtual memory.

</details>

---

<details>
<summary><strong>Hint 4/4</strong></summary>

Memory will only get you so far - be prepared to do some debugging.

<details>
<summary><strong>Be explicit - what does this mean?</strong></summary>

The _"flag"_ is only ever held in memory as plain-text after the password is checked. The password itself is never held in memory as plain-text (its not hashed - it is "retrievable" - but its never left hanging out there to be discovered by memory dumping).

Both the flag and password share a protective mechanism that will likely make memory dumping a harder statergy than debugging to extract these values. However remember that debugging, if done wrong, might impact the integrity mechanism and have other concsequences.

</details>


</details><!-- Hint #4/N -->

</details><!-- Hint #3/N -->

</details><!-- Hint #2/N -->

</details><!-- Hint #1/N -->

---

## Alternative Links

- [Flag #4 Walkthrough](../walk-through/flag4.md) - Still stuck; heres **a solution for this flag**.
- [Flag #4 Design](../design/flag4.md) - A quick talk through **the design and implementation of this flag**.