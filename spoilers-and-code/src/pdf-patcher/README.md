# PDF Patcher (`pdf`)

Build tool used to manipulate and finalise PDF files in the CV CTF.

The source for this project is in the [`./spoilers-and-code/src/pdf-patcher`](./) directory.

## Dependencies

| Dependency Name | Description |
| -- | -- | 
| [`pymupdf`](https://pymupdf.readthedocs.io/en/latest/) | Used to modify PDF files. |
| [`qrcode`](https://pypi.org/project/qrcode/) | Used to generate QR codes. |
| [`csscolor`](https://github.com/idmillington/csscolor) | Used to strings into colours - used to stylise the QR code. |

## Setup

Consider creating a dedicated Python virtual environment for this tool.

```shell
# create a virtual environment
python -m venv venv

# update the pip package manager
venv/bin/python -m pip install --upgrade pip

# install this project (editable)
venv/bin/python -m pip install -e .
```

## Usage

Registers as top-level `pdfp` python module; accessable from command line with usage as:

```shell
venv/bin/python -m pdfp [-l {debug|info|warn|error}] { command... }
```
The following commands are available (use `python -m pdfp {command} --help` for information about arguments)

| Command | Description |
| ---- | ---- |
| `insert-image-with-data` | Inserts an image into a PDF document that includes arbitrary data appended to its PDF data stream. This is used to hide/insert a ZIP file to an image in the CV document. |
| `insert-rectangle` | Inserts a rectangle primitive into a ZIP file. Mostly used for testing and configuring (working out the rectangle you want to use to set when inserting an image or QR code). |
| `insert-qr-code` | Inserts a QR code into a PDF document. |
| `version-layered-pdf` | Creates a PDF document with multiple "layers" or versions. This is used to hide flag #2 under the CV document proper. |