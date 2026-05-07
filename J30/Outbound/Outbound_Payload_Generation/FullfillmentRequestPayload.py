import logging
from datetime import datetime, timedelta
import pandas as pd
import sys
from pathlib import Path

from Outbound.MHE_Journal_Outbound import CURRENT_DIR

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Inbound.Inbound_payload_generation.Number_Generation import NumberGeneration

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class FR_Order_Creation_Payload:
    def __init__(self):
        self.worksheet_data = Outbound_Worksheet()
        self.number_gen = NumberGeneration()
        self.all_fr_order_payloads = []
        self.po_nbr = self.number_gen.purchase_order_number()

    def _parse_order_line_item