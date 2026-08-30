import logging
from pathlib import Path

from Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet as BaseWorksheet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
AUSTRALIA_IMPACT_ROOT = SCRIPT_DIR.parent.parent
AU_INPUT_DIR = AUSTRALIA_IMPACT_ROOT / "Input_files"


def _resolve_default_excel_path() -> Path:
    canonical_file = AU_INPUT_DIR / "Inbound_worksheet.xlsx"
    if canonical_file.is_file():
        return canonical_file
    return canonical_file


class Worksheet(BaseWorksheet):
    """
    Australia Impact wrapper for worksheet reads.
    Reads only from Australia_Impact/Input_files.
    """

    def __init__(self, excel_path=None, master_path=None):
        resolved_excel_path = Path(excel_path) if excel_path else _resolve_default_excel_path()
        resolved_master_path = Path(master_path) if master_path else _resolve_default_excel_path()
        super().__init__(excel_path=resolved_excel_path, master_path=resolved_master_path)
