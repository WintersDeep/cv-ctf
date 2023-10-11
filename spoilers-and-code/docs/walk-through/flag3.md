# Flag #3: I keep the next flag in my treasure.

The flag is in an encrypted ZIP file which is appended to the treasure chest image data stream. You can't just unzip the PDF to access the ZIP due to the way its encoded in that data stream, so you'll have to extract the images raw data.

There are probably several tools for this, but I am going to use [`pdf-parser.py`](https://blog.didierstevens.com/programs/pdf-tools/) to do the dirty work and [`pdfimages`](https://linux.die.net/man/1/pdfimages) to find the image itself in the PDF.

First we use [`pdfimages`](https://linux.die.net/man/1/pdfimages) to locate the image we are interested in. The following command lists all images in the document, and some statistic/information about them:

```bash
glim@ephemeral014:~/cv-versions$ pdfimages -list cv-version-1.pdf
page   num  type   width height color comp bpc  enc interp  object ID x-ppi y-ppi size ratio
--------------------------------------------------------------------------------------------
   1     0 image     752  1083  rgb     3   8  jpeg   no       529  0   300   300 11.4K 0.5%
   1     1 smask     752  1083  gray    1   8  image  no       529  0   300   300 22.4K 2.8%
   1     2 image     256   256  rgb     3   8  image  no       531  0   134   133 15.0K 7.8%
   1     3 smask     256   256  gray    1   1  image  no       531  0   134   133 8192B 100%
```

There are not too many images in the document (by design), looking at the size and colour profile makes the third entry a strong candidate. The file size being 15kb is also a bit suspect for such a small image. 

The object ID for the suspect image is 531, this identifies the object in the PDF. We can dump its raw data stream with `pdf-parser.py`.

```bash
glim@ephemeral014:~/cv-versions$ python3 pdf-parser.py -o 531 -f -d obj531.dat cv-version-1.pdf
obj 531 0
 Type: /XObject
 Referencing: 532 0 R
 Contains stream

  <<
    /DecodeParms
    /Type /XObject
    /Subtype /Image
    /Width 256
    /Height 256
    /BitsPerComponent 8
    /SMask 532 0 R
    /ColorSpace /DeviceRGB
    /Length 15364
    /Filter /FlateDecode
  >>

```

Finally we can ask `unzip` to extract the contents of the dat file. Its going to complain a little because the file doesn't immediately look like an archive, but its just grumbling - use the first two flags to unlock its contents:

```bash
glim@ephemeral014:~/cv-versions$ unzip ./obj531.dat
Archive:  ./obj531.dat
warning [./obj531.dat]:  196608 extra bytes at beginning or within zipfile
  (attempting to process anyway)
[./obj531.dat] README password: 
  inflating: README                  
  inflating: crackme                 
  inflating: final-message.zip       
```

The flag, and follow on instructions can be found in `README`.

## Alternative Links

- [Flag #3 Design](../design/flag3.md) - A quick talk through **the design and implementation of this flag**.
- [Flag #4 Hints](../hints/flag4.md) - If you've completed this flag and want **hints for the next flag**.
- [Flag #4 Walkthrough](../walk-through/flag4.md) - Still stuck; heres **a solution for the next flag**.