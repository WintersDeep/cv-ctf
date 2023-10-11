
# python3 imports
from argparse import ArgumentParser
from typing import List, Any, Iterator, TypeVar, Tuple
from pathlib import Path
from itertools import groupby
from random import randint

# third-party imports
from fitz import Rect
from csscolor import parse
from qrcode import QRCode
from qrcode.constants import ERROR_CORRECT_L

# project imports
from pdfp.actions.base import PatchActionBase
from pdfp.common import PdfDocument


## A self type for the @ref QrMatrixCell object class
QrMatrixCellType = TypeVar('QrMatrixCellType', bound='QrMatrixCell')


## Represents a single cell in a QR matrix.
class QrMatrixCell(object):

    ## Creates a new instance of this object.
    #  @param self the instance of the object that is invoking this method.
    #  @param set indicates if this cell should be shaded (set / high).
    #  @param drawn indicates if this cell has been rendered
    def __init__(self, set:bool, drawn:bool=False) -> QrMatrixCellType:
        self.drawn = drawn or not set
        self.set = set


## A self type for the @ref QrMatrix object class.
QrMatrixType = TypeVar('QrMatrixType', bound='QrMatrix')


## Represents the cells of a QR code.
#  Uses an intermediate format for rendering.
class QrMatrix(object):

    ## Creates a new instance of this object.
    #  @param self the instance of the object invoking this method.
    #  @param matrix the matrix of cells which create a QR code.
    def __init__(self, matrix:list[list[bool]]) -> QrMatrixType:
        
        self.matrix_data = []
        self.matrix_size = len(matrix)

        for y in matrix:
            self.matrix_data.append([])
            for x in y:
                cell = QrMatrixCell(x)
                self.matrix_data[-1].append(cell)

    
    ## Yeilds rows from the QR code matrix.
    #  @param self the instance of the object that is invoking this method.
    #  @returns an iterator which yields lists of cells that appear in each row of the QR code.
    def row_iterator(self) -> Iterator[list[QrMatrixCell]]:
        return self.matrix_data.__iter__()
    

    ## Yeilds columns from the QR code matrix.
    #  @param self the instance of the object that is invoking this method.
    #  @returns an iterator which yields lists of cells that appear in each column of the QR code.
    def column_iterator(self) -> Iterator[list[QrMatrixCell]]:
        for x in range(self.matrix_size):
            yield [ self.matrix_data[y][x] for y in range(self.matrix_size) ]
        return
        yield

    ## Yeilds cells from the QR code matrix.
    #  @param self the instance of the object that is invoking this method.
    #  @returns an iterator which yields cells that appear in each row of the QR matrix - tuple is x, y, cell.
    def cells(self) -> Iterator[Tuple[int, int, QrMatrixCell]]:
        for y, row in enumerate(self.matrix_data):
            for x, cell in enumerate(row):
                yield x, y, cell
        return
        yield


## The self type for the @ref MatrixRenderer class
MatrixRendererType = TypeVar('MatrixRendererType', bound='MatrixRenderer')

## Renders a QrMatrix into rectangles.
#  Note this renderer targets a specific "look" - its designed to create a kind of
#  static texture if the rectangles are rendered with transparency. Its how I did
#  my initial POC and I like the look. You could make this just B/W if you omit 
#  transparency, but then this renderer could also be a lot more simple.
class MatrixRenderer(object):


    ## Creates a new instance of the renderer
    #  @param self the instance of the object that is invoking this method.
    #  @param target_rectangle the area that the QR code is being blatted into.
    #  @param qr_size the size of the QR matrix we are going to render.
    def __init__(self, target_rectangle:Rect, qr_size:int) -> MatrixRendererType:
        self.lhs = min(target_rectangle.x0, target_rectangle.x1)
        self.top = min(target_rectangle.y0, target_rectangle.y1)
        self.xscale = abs(target_rectangle.x0 - target_rectangle.x1) / qr_size
        self.yscale = abs(target_rectangle.y0 - target_rectangle.y1) / qr_size


    ## Walks the matrix (either rows or columns) and return continuous blocks or more than 1 cell where at least one is undrawn.
    #  @note if all cells are drawn, or its a singular cell it is not omitted as otherwise all cells are yielded - I'm aiming for a static texture. This
    #    iterator is designed to intentionally miss those cells - its not a bug. They might be picked up by the next block (row/column) or on the "single"
    #    cell final iteration. Any cell yielded is assumed to have been rendered. This iterator is not aware of whether its iterating rows or columns, it
    #    doesn't care.
    #  @param self the instance of the object that is invoking this method.
    #  @param block_enumerator the row/column enumerator.
    #  @returns an iterator that yields the block index, and cell range of continuous blocks containing undrawn cells.
    def _block_walker(self, block_enumerator:Iterator[list[int]]) -> Iterator[tuple[int, int, int]]:
        
        test_is_high = lambda cell: cell.set
        test_not_drawn = lambda cell: not cell.drawn

        for block_index, block in enumerate(block_enumerator):

            current_cell_offset = 0

            for is_high, cells in groupby(block, test_is_high):
                
                cell_list = list(cells)
                number_of_cells = len(cell_list)

                if is_high and number_of_cells > 1 and any( map(test_not_drawn, cell_list) ):
                    yield block_index, current_cell_offset, current_cell_offset + number_of_cells
                    for cell in cell_list: cell.drawn = True

                current_cell_offset += number_of_cells

        return
        yield

    ## Converts X1,Y1, X2, Y2 cell ranges into graphical rectangles.
    #  @param self the instance of the object invoking this method.
    #  @param x1 the X coordinate of the matrix cell at one corner of the rectangle.
    #  @param y1 the Y coordinate of the matrix cell at one corner of the rectangle.
    #  @param x2 the X coordinate of the matrix cell at the other corner of the rectangle.
    #  @param y2 the Y coordinate of the matrix cell at the other corner of the rectangle.
    #  @returns a rectangle covering the requested region.
    def create_rectangle(self, x1:int, y1:int, x2:int, y2:int) -> Rect:
        return Rect(
            self.lhs + (x1 * self.xscale),
            self.top + (y1 * self.yscale),
            self.lhs + (x2 * self.xscale),
            self.top + (y2 * self.yscale)
        )

    ## Converts the given @ref QrMatrix into a list of rectangles that express it.
    #  @param self the instance of the object that is invoking this method.
    #  @param matrix the matrix to render.
    #  @returns A list of rectangles that draw the given QR matrix.
    def render(self, matrix:QrMatrix) -> list[Rect]:
        
        rectangles = []

        # traverse rows for cell ranges.
        for y, x1, x2 in self._block_walker(matrix.row_iterator()):
            rectangles.append( self.create_rectangle(
                x1, y, x2, y + 1
            ))

        # traverse columns for cell ranges.
        for x, y1, y2 in self._block_walker(matrix.column_iterator()):
            rectangles.append( self.create_rectangle(
                x, y1, x + 1, y2
            ))

        # and colour in singles that dont fall into a continuous range.
        for x, y, cell in matrix.cells():
            if cell.set and not cell.drawn:
                cell.drawn = True
                rectangles.append( self.create_rectangle(
                    x, y, x+1, y+1
                ))

        return rectangles



## Inserts a QR code into the document with the given message.
#  The QR code will be injected as a collection of overlapping rectangles. This prevent trivial extraction of 
#  the code using asset dumping. Because that would be too easy right?
class InsertQrCodeMessage(PatchActionBase):


    ## The string entered on the CLI to invoke this action.
    cli_command = "insert-qr-code"

    ## The help string presented on the CLI for this action when `--help` is used.
    cli_help = "inserts a QR code into the document, built from rectangles."


    ## Optional method derived classes can use to customise arguments for their specific action.
    #  This method is invoked by `PdfPatcherArgs` when it is building an instance of itself.
    #  @param argument_parser to subparser created for this commands arguments.
    @classmethod
    def configure_cli_parser(cls, argument_parser:ArgumentParser) -> None:
        argument_parser.add_argument('pdf', metavar="PDF", type=argument_parser.PdfType, help="The PDF to insert image into.")
        argument_parser.add_argument('x1', type=int, help="Location to insert the image (X coordinate of the first corner).")
        argument_parser.add_argument('y1', type=int, help="Location to insert the image (Y coordinate of the first corner).")
        argument_parser.add_argument('x2', type=int, help="Location to insert the image (X coordinate of the second corner).")
        argument_parser.add_argument('y2', type=int, help="Location to insert the image (Y coordinate of the second corner).")
        argument_parser.add_argument('message', type=str, help="The image file to insert.")
        argument_parser.add_argument('out_file', metavar="PDF-OUT", type=Path, help="The location to write the new PDF with integrity values patched." )
        argument_parser.add_argument('-p', '--page', type=int, default=0, help="The location to write the new PDF with integrity values patched." )
        argument_parser.add_argument('-f', '--fill', type=parse.color, default=parse.color("rgba(255, 102, 0, 0.6)"), help="The fill color of QR code rectangles." )
        argument_parser.add_argument('-s', '--stroke', type=parse.color, default=parse.color("rgba(255, 102, 0, 0.8)"), help="The stroke color of QR code rectangles." )


    ## The PDF document data was loaded from.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the current PDF document data is being loaded from.
    @property
    def pdf(self) -> PdfDocument:
        return self.arguments.pdf
    
    ## Returns the target rectangle for this action.
    #  @param self the instance of the object that is invoking this method.
    #  @returns the rectangle 
    def target_rect(self) -> Rect:
        return self.create_rectangle(
            self.arguments.x1,
            self.arguments.y1,
            self.arguments.x2,
            self.arguments.y2
        )


    ## Builds the a QR code for the given message (but doesn't render it).
    #  @param self the instance of the object that is invoking this method.
    #  @param message the message string to encode in the QR code.
    #  @returns a QRCode object that expresses the given message.
    def get_qr_code(self, message:str) -> QRCode:
        qr = QRCode(
            version=None,                       # let library pick this appropriately for us
            error_correction=ERROR_CORRECT_L,   # not in a medium that is going to suffer damage - cheap out.
            box_size=1,                         # box size doesn't matter in usage context - arbitrary.
            border=0)                           # no order - we'll handle that ourselves
        qr.add_data(message)
        qr.make(fit=True)
        return qr
    

    ## Creates a QR matrix of for the CLI specified message string.
    #  @param self the instance of the object that is invoking this method.
    #  @returns A @ref QrMatrix object that expresses the QR code required to represent the message.
    def get_message_qrcode_matrix(self) -> QrMatrix:
        qr = self.get_qr_code(self.arguments.message)
        output_matrix = qr.get_matrix()
        return QrMatrix(output_matrix)
    

    ## Converts CLI arguments into a dict that will work as kwargs to `Page.draw_rect`
    #  @param self the instance of the object that is invoking this method.
    #  @returns dictionary of items we can use as keywords to render rectangle
    def get_rectangle_render_args(self) -> dict:
        return {
            "color": [ c / 255 for c in self.arguments.stroke.as_int_triple() ], 
            "fill":  [ c / 255 for c in self.arguments.fill.as_int_triple() ],
            "stroke_opacity": self.arguments.stroke.a,
            "fill_opacity": self.arguments.fill.a
        }

    ## Invokes this action on the provided configuration..
    #  This action replaces strings in the target document.
    #  @returns patch process exit code.
    def __call__(self) -> int:

        exit_code = PatchActionBase.ExitSuccess

        self.log.info(f"Starting JPEG insertion in '{self.pdf.path}'.")
        
        try:

            # load operation parameters
            rect = self.target_rect()
            page = self.pdf.load_page(self.arguments.page)
            render_args = self.get_rectangle_render_args()
            qr = self.get_message_qrcode_matrix()

            # convert matrix to a list or rectangles...
            renderer = MatrixRenderer(rect, qr.matrix_size)
            rectangles = renderer.render(qr)

            # render rectangles in a random order.
            while rectangles:
                index = randint(0, len(rectangles) - 1)
                rectangle = rectangles.pop(index)
                page.draw_rect(rectangle, **render_args)                       

            # flush to disk
            self.log.info(f"Finished inserting QR code in '{self.pdf.path}'.")       
            self.pdf.save(self.arguments.out_file)

        except RuntimeError as ex:
            self.log.error(ex)
            exit_code = PatchActionBase.ExitRuntimeError
        
        return exit_code
