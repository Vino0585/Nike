"""
Record TMS UI elements while you execute the flow manually.

Usage:
  python3 Australia_Impact/Outbound/2_TMS_Record_Elements.py

Then:
  1) Perform the TMS steps manually in the opened browser.
  2) Every click is captured with role/text/xpath/playwright locator hints.
  3) Press Enter in this terminal when finished.
  4) Share the output file so automation can be updated accurately.

Output:
  Australia_Impact/Output_files/tms_manual_element_recording.jsonl
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

TMS_URL = "https://nika-aztms-sso-ts1.jdadelivers.com/tm/framework/Frame.jsp"
SMARTBENCH_URL = (
    "https://nika-aztms-sb-ts1.jdadelivers.com/tmria/lbp.jsp"
    "?locale=en_US&returnURL=https://nika-aztms-sso-ts1.jdadelivers.com:443/tm"
)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
OUTPUT_FILE = PROJECT_ROOT / "Output_files" / "tms_manual_element_recording.jsonl"
CHROMIUM_STABILITY_ARGS = [
    "--disable-crash-reporter",
    "--disable-crashpad",
    "--disable-breakpad",
]

CLICK_CAPTURE_SCRIPT = """
() => {
  if (window.__tmsRecorderInstalled) {
    return;
  }
  window.__tmsRecorderInstalled = true;

  const trim = (value, max = 160) => (value || "").trim().slice(0, max);

  const isVisible = (el) => {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 &&
      style.visibility !== "hidden" && style.display !== "none";
  };

  const xpath = (el) => {
    if (!el || el.nodeType !== 1) return "";
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1) {
      let index = 1;
      let sibling = node.previousElementSibling;
      while (sibling) {
        if (sibling.tagName === node.tagName) index += 1;
        sibling = sibling.previousElementSibling;
      }
      const tag = node.tagName.toLowerCase();
      const role = node.getAttribute("role");
      const piece = role ? `${tag}[@role='${role}'][${index}]` : `${tag}[${index}]`;
      parts.unshift(piece);
      if (tag === "html") break;
      node = node.parentElement;
    }
    return "/" + parts.join("/");
  };

  const parentChain = (el, depth = 6) => {
    const chain = [];
    let node = el;
    for (let i = 0; depth > 0 && node; i += 1, node = node.parentElement) {
      chain.push({
        tag: node.tagName,
        role: node.getAttribute("role"),
        ariaLabel: node.getAttribute("aria-label"),
        text: trim(node.innerText, 80),
      });
    }
    return chain;
  };

  const playwrightHints = (el) => {
    const role = el.getAttribute("role");
    const text = trim(el.innerText, 120);
    const ariaLabel = trim(el.getAttribute("aria-label"), 120);
    const name = trim(el.getAttribute("name"), 120);
    const hints = [];
    if (role && (text || ariaLabel)) {
      hints.push(`get_by_role("${role}", name="${text || ariaLabel}")`);
    }
    if (role) {
      hints.push(`locator("[role='${role}']")`);
    }
    if (name) {
      hints.push(`locator("[name='${name}']")`);
    }
    if (el.id) {
      hints.push(`locator("#${el.id}")`);
    }
    return hints;
  };

  const describe = (target) => {
    const el = target.closest(
      "[role], button, input, select, textarea, a, label, div[role], span[role], li"
    ) || target;
    const rect = el.getBoundingClientRect();
    return {
      tag: el.tagName,
      id: el.id || null,
      role: el.getAttribute("role"),
      ariaLabel: el.getAttribute("aria-label"),
      ariaChecked: el.getAttribute("aria-checked"),
      ariaSelected: el.getAttribute("aria-selected"),
      ariaHaspopup: el.getAttribute("aria-haspopup"),
      name: el.getAttribute("name"),
      type: el.getAttribute("type"),
      text: trim(el.innerText, 160),
      className: trim(el.className, 200),
      rect: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
      },
      xpath: xpath(el),
      parentChain: parentChain(el),
      playwrightHints: playwrightHints(el),
      pageTitle: document.title,
      pageUrl: location.href,
    };
  };

  document.addEventListener(
    "click",
    (event) => {
      const target = event.target;
      if (!isVisible(target)) return;
      const payload = describe(target);
      if (window.recordTmsClick) {
        window.recordTmsClick(payload);
      }
    },
    true
  );
}
"""


def _launch_browser(playwright_instance):
    launch_attempts = [
        {"name": "bundled Chromium", "kwargs": {"headless": False, "args": CHROMIUM_STABILITY_ARGS}},
        {"name": "system Chrome channel", "kwargs": {"channel": "chrome", "headless": False}},
    ]
    last_error = None
    for attempt in launch_attempts:
        try:
            browser = playwright_instance.chromium.launch(**attempt["kwargs"])
            print(f"Browser launch succeeded via {attempt['name']}.")
            return browser
        except Exception as exc:
            last_error = exc
            print(f"Browser launch failed via {attempt['name']}: {exc}")
    raise RuntimeError(f"Unable to launch browser: {last_error}")


def _append_recording(record: dict) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def _install_recorder_on_frame(frame) -> None:
    try:
        if frame.is_detached():
            return
        frame.evaluate(CLICK_CAPTURE_SCRIPT)
    except PlaywrightError:
        # Frame navigated or was destroyed mid-injection; safe to ignore.
        return
    except Exception:
        return


def _install_recorder_on_all_frames(page) -> None:
    for frame in page.frames:
        _install_recorder_on_frame(frame)


def _setup_recording_handlers(page) -> None:
    def on_frame_attached(frame) -> None:
        _install_recorder_on_frame(frame)

    page.on("frameattached", on_frame_attached)


def run_recorder(start_url: str) -> None:
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    recordings: list[dict] = []
    click_counter = 0

    def on_click(payload: dict) -> None:
        nonlocal click_counter
        click_counter += 1
        record = {
            "clickNo": click_counter,
            "capturedAt": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        recordings.append(record)
        _append_recording(record)
        print(f"\n[Recorded click #{click_counter}]")
        print(f"  role={record.get('role')} text={record.get('text')!r}")
        print(f"  aria-checked={record.get('ariaChecked')} aria-selected={record.get('ariaSelected')}")
        print(f"  xpath={record.get('xpath')}")
        if record.get("playwrightHints"):
            print(f"  hint={record['playwrightHints'][0]}")

    print("Starting TMS element recorder.")
    print(f"Output file: {OUTPUT_FILE}")
    print("Open the browser, execute TMS manually, then return here and press Enter to finish.")
    print("If no clicks appear below, the page may still be loading or using a nested frame.\n")

    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        context = browser.new_context()
        # Init script runs automatically on every navigation and in every new frame/document.
        context.add_init_script(CLICK_CAPTURE_SCRIPT)
        context.expose_function("recordTmsClick", on_click)
        page = context.new_page()
        _setup_recording_handlers(page)
        page.goto(start_url, wait_until="domcontentloaded")
        _install_recorder_on_all_frames(page)

        input("Recording... press Enter here when manual TMS flow is complete: ")
        # Re-inject after manual navigation (e.g. SSO redirect) before closing.
        _install_recorder_on_all_frames(page)

        summary = {
            "finishedAt": datetime.now(timezone.utc).isoformat(),
            "totalClicks": click_counter,
            "outputFile": str(OUTPUT_FILE),
        }
        print("\nRecording complete.")
        print(json.dumps(summary, indent=2))
        if click_counter == 0:
            print(
                "\nNo clicks were captured. Re-run the recorder and confirm click lines appear "
                "in this terminal while you work in the browser."
            )
        context.close()
        browser.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record TMS UI elements during manual execution.")
    parser.add_argument(
        "--start-url",
        default=None,
        help="URL to open before recording (overrides --smartbench).",
    )
    parser.add_argument(
        "--smartbench",
        action="store_true",
        help="Start directly at Transportation Smartbench (use after SSO is already done).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    start_url = args.start_url or (SMARTBENCH_URL if args.smartbench else TMS_URL)
    run_recorder(start_url=start_url)
