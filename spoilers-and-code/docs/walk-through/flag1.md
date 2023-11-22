# Flag #1: Got too close to sensative information.

The flag is hidden "underneath" the redaction graphic.

Most PDF reader software will let you select it using your cursor, afterwhich you can copy and paste it like normal text into another editor.

If you're feeling terminal today and have [`pdftotext`](https://linux.die.net/man/1/pdftotext) installed you can also pull it directly out the CV with.

```bash
glim@ephemeral014:~$ pdftotext cv.pdf - | grep -i flag | head -n 1
FLAG 1: FLAG1DEBUG
```

In practise you wouldn't know the string to look for, or that it would be the first to be returned by the above query so would either have to guess `grep` strings or manually sift the results.

You would also want to examine the surrounding text for the "hint" for the next flag (consider using `-A` and `-B` flags when using grep).

## Alternative Links

- [Flag #1 Design](../design/flag1.md) - A quick talk through **the design and implementation of this flag**.
- [Flag #2 Hints](../hints/flag2.md) - If you've completed this flag and want **hints for the next flag**.
- [Flag #2 Walkthrough](../walk-through/flag2.md) - Still stuck; heres **a solution for the next flag**.