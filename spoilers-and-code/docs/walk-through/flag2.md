# Flag #2: I did a better job removing this one.

The flag is hidden in a previous version of the document.

There are a number of tools and services you can use to extract this (although I would really appreciate it if you didn't upload my CV to random websites). I would personally suggest [`pdfressurect`](https://manpages.ubuntu.com/manpages/focal/man1/pdfresurrect.1.html)

```bash
glim@ephemeral014:~$ pdfresurrect -w cv.pdf
glim@ephemeral014:~$ ls -lah cv-versions/
drwx------ 2 glim glim 4.0K Jun  6 22:26 .
drwxrwxr-x 3 glim glim 4.0K Jun  6 22:26 ..
-rw-rw-r-- 1 glim glim 309K Jun  6 22:26 cv-version-1.pdf
-rw-rw-r-- 1 glim glim 309K Jun  6 22:26 cv-version-2.pdf
-rw-rw-r-- 1 glim glim  62K Jun  6 22:26 cv-versions.summary
```

This will present you with something like this...

![Preview of the flag #2 hidden layer](./images/flag2-example.png "Flag #2 hidden layer example.")

Scan the QR code for instructions for flag #3.

## Alternative Links

- [Flag #2 Design](../design/flag2.md) - A quick talk through **the design and implementation of this flag**.
- [Flag #3 Hints](../hints/flag3.md) - If you've completed this flag and want **hints for the next flag**.
- [Flag #3 Walkthrough](../walk-through/flag3.md) - Still stuck; heres **a solution for the next flag**.