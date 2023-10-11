# Flag #2: I did a better job removing this one.

Many people are not aware that PDF's support incremental saves. When using this feature rather than save the state of the document, only the changes from the previous save state are saved. This can allow a inquisitive party to see previous versions of a file that might include sensative notes, comments or details that were later removed.

This mechanic is a fundemental part of PDF that is supported by all readers; however it doesn't seem to recieve much use or implementation in writers.

I've used this mechanic to build an entirely seperate document _"under"_ the CV itself. 

To ensure that the flag doesn't leak with tools that extract text and do not respect version history, such as might be used to capture the previous flag I've used a QR code to present the flag. Images are equally at risk of being extracted in an automated manner, so to prevent this the QR _"image"_ is actually programatically built up from overlapping rectangle primitives. These are not usually extracted from documents and even if they were to be, are completely meaningless in isolation.

This flag is generally considered little trickier than the previous one because it requires some knowledge/understanding of PDF files.

## Considerations / Other Ideas / Suggestions

> No one has made any suggestions to change/enhance this flag and I have no discarded ideas related to it. 

## Alternative Links

- [Flag #2 Walk Through](../walk-through/flag2.md) - Still stuck; heres **a solution for this flag**.
- [Flag #3 Hints](../hints/flag3.md) - If you've completed this flag and want **hints for the next flag**.
- [Flag #3 Design](./flag3.md) - If you've completed this flag and want **a solution for the next flag**.