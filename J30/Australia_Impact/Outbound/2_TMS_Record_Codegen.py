"""
Launch Playwright codegen to record the full TMS manual flow.

This is more reliable than click-listener injection because Smartbench
uses cross-origin frames where in-page listeners often miss clicks.

Usage:
  python3 Australia_Impact/Outbound/2_TMS_Record_Codegen.py

Steps:
  1) Playwright Inspector opens with a browser.
  2) Perform the full TMS flow manually for shipment TEST091000028.
  3) Close the Inspector window when finished.
  4) Tell the agent "codegen done" to convert the recording into 2_TMS_Process.py

Output:
  Australia_Impact/Output_files/tms_codegen_recorded.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

TMS_URL = "https://nika-aztms-sso-ts1.jdadelivers.com/tm/framework/Frame.jsp"
SMARTBENCH_URL = (
    "https://nika-aztms-sb-ts1.jdadelivers.com/tmria/lbp.jsp"
    "?locale=en_US&returnURL=https://nika-aztms-sso-ts1.jdadelivers.com:443/tm"
)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
OUTPUT_FILE = PROJECT_ROOT / "Output_files" / "tms_codegen_recorded.py"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record TMS flow with Playwright codegen.")
    parser.add_argument(
        "--smartbench",
        action="store_true",
        help="Start at Smartbench URL instead of TMS login URL.",
    )
    return parser.parse_args()


def main() -> None:
    if shutil.which("playwright") is None:
        raise RuntimeError("Playwright CLI not found. Install with: pip install playwright")

    args = _parse_args()
    start_url = SMARTBENCH_URL if args.smartbench else TMS_URL
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "playwright",
        "codegen",
        "--channel",
        "chrome",
        "-o",
        str(OUTPUT_FILE),
        start_url,
    ]

    print("Launching Playwright codegen recorder.")
    print(f"Start URL: {start_url}")
    print(f"Output file: {OUTPUT_FILE}")
    print("Perform the TMS flow in the browser, then close the Inspector to save.\n")

    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    if OUTPUT_FILE.exists():
        print(f"\nCodegen recording saved to: {OUTPUT_FILE}")
    else:
        print("\nNo output file was created. Close the Inspector after recording to save.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
