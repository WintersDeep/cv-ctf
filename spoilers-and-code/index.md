# Warning: Spoilers Ahead

<img src="./docs/images/stop-warning.svg" style="text-align:center; width: 50%;"></img>

**Beyond this directory you will find source code, build tools, design information, and other resources related to the CV CTF.**

If you intend to attempt completing the CTF unassisted, proceeding beyond this point is not recommended. 

<details>
<summary><strong>I understand, show me the navigation menu</strong></summary>

## [Hints](./docs/hints/flag1.md)
 
This is a good place to start if you actually want to do the CTF solo but are struggling.
 
The hints pages contain leading clues about how to solve the CTF, but stops short of giving you actual answers. As with other sections this is split up per-flag so there isn't any risk in spoiling one flag by looking at hints for another. Hints are provided one at a time to prevent giving too much information all at once.

## [Walk-Through](./docs/walk-through/flag1.md)

The walk through pages hand-hold you through solving most of the CTF.

They describe in very brief terms where the flag is hidden, and how you go about extracting it. As with other sections this is split up per-flag so if you get stuck and just need an answer you can use a walk-through to get on and try your hand at the next one. The only flag without an explicit answer is the final one, but there is still some supporting material.

## [Flag Design](./docs/design/flag1.md)

The design pages discuss in detail how each flag is hidden.

They also discuss why its implemented in the way it is, the types of idea that I considered but discarded (and why). This is mostly for reference, but can be useful as an intermediary between the hints and the walk-through (as in; being told exactly what the adversary is and how it works, but not explictly how to deal with it).

## [Source Code and Build Tools](./src/)

This directory contains the source code and build tools.

This isn't a fully working solution - the build process requires artifacts that are not checked in (mostly the actual CV or PII elements themselves unsurprisingly). Documentation is sparse, but this isn't a production system or something designed for distribution. I found aspects of the CTF where sometimes touched upon during interview and having the code available would be benefitial to facilitate those discussions. 
 

</details>