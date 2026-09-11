import json
import random
from datetime import datetime
from pathlib import Path


class NumberGeneration:
    _FR_ORDER_STATE_FILE = Path(__file__).resolve().with_name(".fr_order_sequence_state.json")

    def __init__(self):
        self.generated_fr_order_ids = []
        self.generated_po_ids = None

    @classmethod
    def _next_fr_order_sequence(cls, date_key: str) -> int:
        state = {}
        if cls._FR_ORDER_STATE_FILE.exists():
            try:
                state = json.loads(cls._FR_ORDER_STATE_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                state = {}

        stored_date = None
        stored_counter = 0
        if isinstance(state, dict):
            if "date_key" in state and "counter" in state:
                stored_date = str(state.get("date_key"))
                stored_counter = int(state.get("counter", 0))
            elif date_key in state:
                stored_date = date_key
                stored_counter = int(state.get(date_key, 0))

        next_sequence = 1 if stored_date != date_key else stored_counter + 1
        try:
            cls._FR_ORDER_STATE_FILE.write_text(
                json.dumps({"date_key": date_key, "counter": next_sequence}),
                encoding="utf-8",
            )
        except OSError:
            pass
        return next_sequence

    def fr_order_number_generation(self, num_of_order_to_generate: int, _envn: str, initial: str):
        if not isinstance(num_of_order_to_generate, int) or num_of_order_to_generate <= 0:
            return []

        self.generated_fr_order_ids = []
        timestamp = datetime.now().strftime("%m%d")
        date_key = datetime.today().strftime("%m%d%Y")
        for _ in range(num_of_order_to_generate):
            sequence = self._next_fr_order_sequence(date_key)
            self.generated_fr_order_ids.append(f"{initial}{timestamp}{sequence:05d}")
        return self.generated_fr_order_ids

    def purchase_order_number(self):
        self.generated_po_ids = f"PO{datetime.today().strftime('%m%d')}{random.randint(1000, 9999)}"
        return self.generated_po_ids
