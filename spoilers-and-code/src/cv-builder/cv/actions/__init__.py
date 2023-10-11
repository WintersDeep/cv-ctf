# project imports
from .build_crackme_internal import BuildCrackmeInternalAction
from .build_crackme_patch import BuildCrackmePatchAction
from .build_crackme_launcher import BuildCrackmeLauncherAction
from .build_crackme import BuildCrackmeAction
from .build_final_message_zip import BuildFinalMessageZip
from .build_flag3_zip import BuildFlag3Zip
from .build_pdf_hidden_layer import BuildPdfHiddenLayer
from .build_layered_pdf import BuildLayeredPdf
from .build import Build
from .export_public import ExportPublicAction

## A list of actions this tool can perform.
available_actions = [
    BuildCrackmeInternalAction,
    BuildCrackmePatchAction,
    BuildCrackmeLauncherAction,
    BuildCrackmeAction,
    BuildFinalMessageZip,
    BuildFlag3Zip,
    BuildPdfHiddenLayer,
    BuildLayeredPdf,
    Build,
    ExportPublicAction
]