import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STATE_DIR = Path(__file__).resolve().parent
STATE_FILE = STATE_DIR / ".inbound_sequence_state.json"
LEGACY_STATE_FILE = (
    Path(__file__).resolve().parent.parent.parent / "Input_files" / "Automation_State.json"
)


class StateManager:
    """
    Shared persistent state manager for Australia inbound automation.
    Supports both generic key/value storage and reusable counters.
    """

    def __init__(self, state_file: Path | None = None):
        self.state_file = state_file or STATE_FILE
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_state_if_needed()

    def _default_state(self) -> dict:
        return {
            "counters": {
                "lpn_sequence_state": 0,
                "trailer_nbr": 0,
                "asn_nbr": 0,
                "lpn_number": 0,
                "pallet_nbr": 0,
            },
            "values": {},
            "metadata": {
                "description": "Australia inbound shared sequence/runtime state",
            },
        }

    def _migrate_legacy_state_if_needed(self):
        if self.state_file.exists() or not LEGACY_STATE_FILE.exists():
            return
        try:
            with open(LEGACY_STATE_FILE, "r", encoding="utf-8") as legacy_handle:
                legacy_state = json.load(legacy_handle)
            if not isinstance(legacy_state, dict):
                legacy_state = self._default_state()
        except Exception:
            legacy_state = self._default_state()
        self._write_state(legacy_state)

    def _read_state(self) -> dict:
        if not self.state_file.exists():
            default_state = self._default_state()
            self._write_state(default_state)
            return default_state
        try:
            with open(self.state_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
        except Exception as ex:
            logging.error(f"Failed to read automation state file '{self.state_file}': {ex}")
        return self._default_state()

    def _write_state(self, state: dict):
        try:
            with open(self.state_file, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2)
        except Exception as ex:
            logging.error(f"Failed to write automation state file '{self.state_file}': {ex}")

    def get_value(self, key: str, default: Any = None) -> Any:
        state = self._read_state()
        return state.get(key, default)

    def set_value(self, key: str, value: Any):
        state = self._read_state()
        state[key] = value
        self._write_state(state)

    def increment_counter(
        self,
        counter_name: str,
        start: int = 1,
        min_value: int = 1,
        max_value: int = 99,
        scope: str | None = None,
    ) -> int:
        """
        Increment and persist a named counter.
        Optional scope lets callers isolate counters (e.g. by date).
        """
        state = self._read_state()
        counters = state.setdefault("counters", {})
        counter_key = f"{counter_name}:{scope}" if scope else counter_name

        current = counters.get(counter_key, start - 1)
        try:
            current = int(current)
        except (ValueError, TypeError):
            current = start - 1

        next_value = current + 1
        if next_value > max_value:
            next_value = min_value

        counters[counter_key] = next_value
        state["counters"] = counters
        self._write_state(state)
        return next_value
