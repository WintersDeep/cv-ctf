# project imports
from .insert_image_with_trailing_data import InsertImageWithTrailingData
from .insert_rectangle import InsertRectangle
from .insert_qr_code_message import InsertQrCodeMessage
from .version_layered_pdf import VersionLayeredPDF

## A list of actions this tool can perform.
available_actions = [
    InsertImageWithTrailingData,
    InsertRectangle,
    InsertQrCodeMessage,
    VersionLayeredPDF
]