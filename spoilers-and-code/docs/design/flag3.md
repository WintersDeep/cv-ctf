# Flag #3: I keep the next flag in my treasure.

This flag is a ZIP file which is appended to the data for the treasure chest image in the same way that you might hide a ZIP after a PNG/JPEG.

This one is a little trickier to extract however. Whilst PDF is a vector format, it doesn't just insert an image file. In PDF images are an object and have their own data stream formats. These formats have various encodings and compressions and might in some ways resemble their original file format, but thats about as close as it gets... a resembelance.

If you use off-the-shelf image extractors to pull images out from the PDF they will first need to convert the image objects data stream back into a native file format. As the ZIP data containing the flag is appended and technically _"trailling junk"_ these conversion tools will omit/truncate these bytes (how do you convert something that inherently has no meaning?). You'll get the image, you wont get the ZIP.

To get the ZIP containing the flag, you'll need to dump the raw stream data itself.

## Considerations / Other Ideas / Suggestions

> This flag has twice been cited as one that required hints or support. For the quantity of people who actually attempt the CTF, this makes it quite a high failure rate - I may need to look into how I hint and present this flag, or remove it entirely. 

- Previous versions did have the ZIP/image file as an attachment but this had a couple of drawbacks:
    - It was often considered an easier flag than #2.
    - Some software platforms reject PDFs with attachments; whether those that accept the CV do so because they don't see the attachment (as it technically only appears in a _"previous version"_), or becuase they permit it is in itself an interesting distinction.
- The ZIP in an image gag feels pretty run of the mill, and I hope people are going to get that (esp. with the clue and visual hints) 
- I like the way the ZIP appears to "vanish" if you just extract the image wholesale from the PDF.

## Alternative Links

- [Flag #3 Walk Through](../walk-through/flag3.md) - Still stuck; heres **a solution for this flag**.
- [Flag #4 Hints](../hints/flag4.md) - If you've completed this flag and want **hints for the next flag**.
- [Flag #4 Design](./flag4.md) - If you've completed this flag and want **a solution for the next flag**.