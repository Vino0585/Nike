"""
TMS end-to-end automation — aligned to tms_codegen_recorded.py.

Codegen is the source of truth. This script adds only:
  - FFR shipment ID from latest_created_ffr_numbers.txt
  - Login via TMS URL (same SSO / Smartbench path as codegen)
  - Optional step delays for visible execution
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

from playwright.sync_api import Page, TimeoutError, sync_playwright

TMS_URL = "https://nika-aztms-sso-ts1.jdadelivers.com/tm/framework/Frame.jsp"
SMARTBENCH_TITLE = "Transportation Smartbench"
LOGOUT_URL = "https://tmslogout.jdadelivers.com/logout.htm"
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
FFR_NUMBER_STORE_FILE = PROJECT_ROOT / "Output_files" / "latest_created_ffr_numbers.txt"
CHROMIUM_STABILITY_ARGS = [
    "--disable-crash-reporter",
    "--disable-crashpad",
    "--disable-breakpad",
]


# ---------------------------------------------------------------------------
# Small helpers (not in codegen — infrastructure only)
# ---------------------------------------------------------------------------


def _run_step(step_no: int, description: str, delay: float, action) -> None:
    print(f"[Step {step_no}] {description}")
    action()
    if delay > 0:
        time.sleep(delay)


def _read_shipment_id() -> str:
    if not FFR_NUMBER_STORE_FILE.exists():
        raise FileNotFoundError(
            f"FFR store not found: {FFR_NUMBER_STORE_FILE}. Run 1_FR_Order_Creation.py first."
        )
    value = FFR_NUMBER_STORE_FILE.read_text(encoding="utf-8").strip().split(",")[0].strip()
    if not value:
        raise ValueError(f"FFR store is empty: {FFR_NUMBER_STORE_FILE}")
    return value


def _try_click(locator, timeout_ms: int = 8000) -> bool:
    try:
        if locator.count() == 0:
            return False
        locator.first.click(timeout=timeout_ms)
        return True
    except Exception:
        return False


def _on_smartbench(page: Page) -> bool:
    return SMARTBENCH_TITLE in page.title() or "tmria/lbp.jsp" in page.url


def _wait_for_title(page: Page, titles: list[str], timeout_s: int = 45) -> None:
    end = time.time() + timeout_s
    while time.time() < end:
        if _on_smartbench(page) and SMARTBENCH_TITLE in titles:
            return
        if any(t in page.title() for t in titles):
            return
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for title in: {titles}")


def _launch_browser(playwright):
    for name, kwargs in (
        ("bundled Chromium", {"headless": False, "args": CHROMIUM_STABILITY_ARGS}),
        ("system Chrome", {"channel": "chrome", "headless": False}),
        ("headless Chromium", {"headless": True, "args": CHROMIUM_STABILITY_ARGS}),
    ):
        try:
            browser = playwright.chromium.launch(**kwargs)
            print(f"Browser launch succeeded via {name}.")
            return browser
        except Exception as exc:
            print(f"Browser launch failed via {name}: {exc}")
    raise RuntimeError("Unable to launch browser.")


def _loc(page: Page, primary: str, suffix_fallback: str | None = None):
    """Codegen locator with optional [id$='suffix'] fallback for dynamic isc_* IDs."""
    for selector in (primary, f"[id$='{suffix_fallback}']" if suffix_fallback else None):
        if not selector:
            continue
        loc = page.locator(selector).first
        if loc.count() > 0:
            return loc
    return page.locator(primary).first


# ---------------------------------------------------------------------------
# Login — codegen lines 10-14 adapted for TMS_URL entry
# ---------------------------------------------------------------------------


def _click_sso_if_present(page: Page) -> None:
    """Codegen SSO click — Okta redirect detaches element; don't fail on that."""
    if "Sign in" not in page.title():
        return
    sso = page.get_by_role("link", name="NIKE APLA (SSO)")
    if sso.count() == 0:
        return
    try:
        sso.first.click(timeout=8000, no_wait_after=True)
    except Exception:
        pass


def _click_transportation_smartbench(page: Page) -> None:
    """Codegen line 12 — Firefox: #TREECELL_solutions_1_row link to tmria/lbp.jsp."""
    shell = page.frame_locator('frame[name="i2ui_shell_content"]')
    nav = shell.frame_locator("#navFrame")

    for loc in (
        nav.locator('#TREECELL_solutions_1_row a[href*="tmria/lbp.jsp"]'),
        nav.locator("#TREECELL_solutions_1_row").get_by_role("link", name="Transportation Smartbench"),
        shell.locator('#TREECELL_solutions_1_row a[href*="tmria/lbp.jsp"]'),
        nav.get_by_role("link", name="Transportation Smartbench"),
        shell.get_by_role("link", name="Transportation Smartbench"),
    ):
        try:
            target = loc.first
            target.wait_for(state="visible", timeout=15000)
            target.click(timeout=15000)
            return
        except Exception:
            continue
    raise RuntimeError("Could not find Transportation Smartbench link in TM frames.")


def _login_and_open_smartbench(page: Page) -> None:
    _wait_for_title(page, ["Transportation Manager", SMARTBENCH_TITLE, "Sign in"], timeout_s=45)

    # Codegen line 10-11: SSO (Okta DSSO redirect chain may take time)
    _click_sso_if_present(page)
    _wait_for_title(page, ["Transportation Manager", SMARTBENCH_TITLE, "Sign in"], timeout_s=90)

    # Codegen line 12: open Smartbench from solutions tree
    if "Transportation Manager" in page.title():
        _click_transportation_smartbench(page)
        _wait_for_title(page, [SMARTBENCH_TITLE, "Sign in"], timeout_s=45)

    # Codegen line 13: SSO bounce after Smartbench redirect
    _click_sso_if_present(page)
    _wait_for_title(page, [SMARTBENCH_TITLE], timeout_s=90)

    if not _on_smartbench(page):
        raise RuntimeError(f"Did not reach {SMARTBENCH_TITLE}. Title: {page.title()} URL: {page.url}")


# ---------------------------------------------------------------------------
# Codegen lines 15-22: Smartbench cleanup + Shipment selection + filter
# Literal translation from tms_codegen_recorded.py
# ---------------------------------------------------------------------------


def _smartbench_shipment_selection(page: Page, shipment_id: str) -> None:
    # Line 15: close Shipment tab if open
    try:
        page.get_by_role("tab", name="Shipment (1)").get_by_label("Close").click(timeout=3000)
    except Exception:
        pass

    # Line 16: close Shipment Legs tab if open
    try:
        page.get_by_role("tab", name="Shipment Legs of Shipment").get_by_label("Close").click(timeout=3000)
    except Exception:
        pass

    # Line 17: close any remaining panel
    try:
        page.get_by_role("button", name="Close", exact=True).click(timeout=3000)
    except Exception:
        pass

    # Line 18 — codegen; .last avoids strict match with open Shipment tab label
    page.get_by_text("Shipment", exact=True).last.dblclick()

    # Line 19
    page.locator("div").filter(
        has_text=re.compile(r"^ShipmentLoadsOptimization RequestsUnrouteable Shipments$")
    ).first.click()

    # Lines 20-22 — Shipment ID filter (not DLVD)
    # Firefox inspect: textarea#isc_UM name="shipmentNumber$148l" (id rotates; name is stable)
    shipment_id_filter = page.locator('textarea[name^="shipmentNumber"]')
    shipment_id_filter.click()
    shipment_id_filter.fill(shipment_id)
    shipment_id_filter.press("Enter")

    page.get_by_text(shipment_id, exact=True).first.wait_for(state="visible", timeout=120000)
    print(f"Shipment '{shipment_id}' found in grid.")


def _select_filtered_shipments(page: Page) -> None:
    """Codegen line 23 — Firefox: td.headerButton > #isc_RM > #isc_RN > span[eventpart=valueicon]"""
    clicked = page.evaluate(
        """() => {
            const rn = document.querySelector('td.headerButton #isc_RN')
                || document.querySelector('#isc_RN');
            if (!rn) return false;
            const span = rn.querySelector('span[eventpart="valueicon"]');
            if (!span) return false;
            if (span.classList.contains('checkboxFalse')) span.click();
            return true;
        }"""
    )
    if not clicked:
        # same structure when isc_* id rotates: td.headerButton > span[eventpart=valueicon]
        page.locator("td.headerButton span[eventpart='valueicon']").first.click(
            timeout=8000, force=True
        )
    time.sleep(0.4)
    print("Shipment panel master checkbox selected.")


# ---------------------------------------------------------------------------
# Codegen lines 23-38: Cascade → Legs → Planning → Load → Release
# ---------------------------------------------------------------------------


def _select_shipment_legs_rows(page: Page) -> None:
    # Codegen line 26 — Firefox: #isc_112 > span[eventpart=valueicon] (Legs panel below Shipment)
    clicked = page.evaluate(
        """() => {
            const header = document.querySelector('#isc_112');
            if (!header) return false;
            const span = header.querySelector('span[eventpart="valueicon"]');
            if (!span) return false;
            if (span.classList.contains('checkboxFalse')) span.click();
            return true;
        }"""
    )
    if not clicked:
        page.locator("td.headerButton span[eventpart='valueicon']").last.click(
            timeout=8000, force=True
        )
    time.sleep(0.5)
    print("Shipment Legs master checkbox selected.")


def _cascade_to_shipment_legs(page: Page) -> None:
    # Codegen lines 24-25
    page.get_by_role("button", name="Cascade").click(timeout=8000)
    page.get_by_text("Shipment Legs").click(timeout=8000)
    time.sleep(0.6)


def _planning_action(page: Page, menu_text: str) -> None:
    page.get_by_role("button", name="Planning Operations").click(timeout=8000)
    page.get_by_text(menu_text, exact=True).click(timeout=8000)
    time.sleep(0.6)


def _submit_optimization_with_po(page: Page) -> None:
    # Codegen lines 31-33 — Firefox: #isc_1CL Constraints Override dropdown
    dialog = page.get_by_label("Create Optimization Request")
    dialog.wait_for(state="visible", timeout=30000)
    constraints = dialog.locator("#isc_1CL")
    if constraints.count() == 0:
        constraints = dialog.locator("div.selectItemLiteText").first
    constraints.click(timeout=8000, force=True)
    time.sleep(0.4)
    page.get_by_text("PO", exact=True).click(timeout=8000)
    time.sleep(0.3)
    page.get_by_label("Create Optimization Request").get_by_role("button", name="Submit").click(
        timeout=10000
    )
    time.sleep(1.0)


def _assign_to_new_load(page: Page) -> None:
    # Codegen lines 33-34
    page.get_by_role("button", name="Load Operations").click(timeout=8000)
    page.get_by_text("Assign to New Load", exact=True).click(timeout=8000)
    time.sleep(0.6)


def _open_loads_panel(page: Page) -> None:
    # Shipment Legs toolbar: Cascade → Loads (do not click Shipment Legs tab — collapses panel)
    cascade = page.locator("td.otherToolStripButton").filter(has_text=re.compile(r"^Cascade$"))
    if cascade.count() > 1:
        cascade.last.click(timeout=8000, force=True)
    else:
        cascade.first.click(timeout=8000, force=True)
    # Click only the visible Loads row from Cascade menu (not hidden DOM copies)
    loads_menu = page.locator("td.menuTitleField").filter(has_text=re.compile(r"^Loads$"))
    loads_clicked = False
    end = time.time() + 15
    while time.time() < end and not loads_clicked:
        for i in range(loads_menu.count()):
            item = loads_menu.nth(i)
            try:
                if item.is_visible():
                    item.click(timeout=5000)
                    loads_clicked = True
                    break
            except Exception:
                continue
        if not loads_clicked:
            time.sleep(0.5)
    if not loads_clicked:
        raise RuntimeError("Visible Loads menu item not found after Cascade on Shipment Legs.")

    page.get_by_role("tab", name=re.compile(r"Load of Shipment Leg")).wait_for(
        state="visible", timeout=30000
    )
    print("Load panel opened.")
    time.sleep(0.6)


def _select_load_panel_rows(page: Page) -> None:
    """Load panel master checkbox — only after Load of Shipment Leg tab is open."""
    page.get_by_role("tab", name=re.compile(r"Load of Shipment Leg")).wait_for(
        state="visible", timeout=10000
    )
    checkbox = page.locator("td.headerButton span[eventpart='valueicon']").last
    if page.locator("td.headerButton .checkboxFalse").count() > 0:
        checkbox.click(timeout=8000, force=True)
    time.sleep(0.4)
    print("Load panel master checkbox selected.")


def _select_load_and_release(page: Page) -> None:
    # Codegen lines 37-38
    _select_load_panel_rows(page)
    page.get_by_role("button", name="Release Shipment Plan").click(timeout=15000)
    time.sleep(0.6)


# ---------------------------------------------------------------------------
# Codegen lines 39-51: Tender
# ---------------------------------------------------------------------------


def _click_visible_tender_operations(page: Page) -> None:
    """Load panel toolbar — Firefox: td.otherToolStripButton Tender Operations."""
    tender_ops = page.locator("td.otherToolStripButton").filter(
        has_text=re.compile(r"^Tender Operations$")
    )
    for i in range(tender_ops.count() - 1, -1, -1):
        btn = tender_ops.nth(i)
        try:
            if btn.is_visible():
                btn.click(timeout=5000)
                return
        except Exception:
            continue
    tender_ops.last.click(timeout=8000, force=True)


def _click_visible_menu_title(page: Page, label: str) -> None:
    """Tender menu row — Firefox: td.menuTitleField nobr (Load Tender / Accept Load Tender)."""
    menu = page.locator("td.menuTitleField").filter(has_text=re.compile(rf"^{label}$"))
    end = time.time() + 30
    while time.time() < end:
        for i in range(menu.count()):
            item = menu.nth(i)
            try:
                if item.is_visible():
                    item.click(timeout=5000)
                    return
            except Exception:
                continue
        time.sleep(0.5)
    menu.last.click(timeout=8000, force=True)


def _tender_load(page: Page) -> None:
    _click_visible_tender_operations(page)
    time.sleep(1.0)
    _click_visible_menu_title(page, "Load Tender")
    _loc(page, "#isc_P2", "_P2").click(timeout=8000)
    page.get_by_text("Auto-Accept Tender", exact=True).click(timeout=8000)
    page.get_by_text("Auto-Accept Tender", exact=True).click(timeout=8000)
    page.get_by_role("textbox", name="Accepted By").fill("VGTest")
    page.get_by_label("Tender for Selected Loads").get_by_role("button", name="Submit").click(
        timeout=10000
    )
    time.sleep(1.0)

    _click_visible_tender_operations(page)
    time.sleep(1.0)
    _click_visible_menu_title(page, "Accept Load Tender")
    page.get_by_role("textbox", name="Accepted By").fill("VGTest")
    page.get_by_label("Tender Accept Selected Loads").get_by_role("button", name="Submit").click(
        timeout=10000
    )
    time.sleep(1.0)


# ---------------------------------------------------------------------------
# Codegen lines 52-56: final cleanup + logout
# ---------------------------------------------------------------------------


def _final_cleanup_and_logout(page: Page) -> None:
    for tab_name in ("Load of Shipment Leg", "Shipment Legs of Shipment"):
        try:
            page.get_by_role("tab", name=tab_name).get_by_label("Close").click(timeout=3000)
            time.sleep(0.3)
        except Exception:
            pass
    _try_click(page.get_by_role("button", name="Close", exact=True), timeout_ms=3000)
    _try_click(page.get_by_role("button", name="Logout"), timeout_ms=5000)
    page.goto(LOGOUT_URL, wait_until="domcontentloaded")


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


def run_tms_process(step_delay_seconds: float = 1.5) -> None:
    shipment_id = _read_shipment_id()
    print(f"Running TMS flow for shipment: {shipment_id}")

    with sync_playwright() as p:
        browser = _launch_browser(p)
        context = browser.new_context()
        page = context.new_page()

        _run_step(1, "Open TMS URL", step_delay_seconds, lambda: page.goto(TMS_URL, wait_until="domcontentloaded"))
        _run_step(2, "Login and open Transportation Smartbench", step_delay_seconds, lambda: _login_and_open_smartbench(page))
        _run_step(
            3,
            "Smartbench: cleanup, open Shipment, filter by Shipment ID",
            step_delay_seconds,
            lambda: _smartbench_shipment_selection(page, shipment_id),
        )
        _run_step(4, "Select filtered shipments (master checkbox)", step_delay_seconds, lambda: _select_filtered_shipments(page))
        _run_step(5, "Cascade to Shipment Legs", step_delay_seconds, lambda: _cascade_to_shipment_legs(page))
        _run_step(6, "Select Shipment Legs (master checkbox)", step_delay_seconds, lambda: _select_shipment_legs_rows(page))
        _run_step(7, "Select for Optimization", step_delay_seconds, lambda: _planning_action(page, "Select for Optimization"))
        _run_step(8, "Optimize", step_delay_seconds, lambda: _planning_action(page, "Optimize"))
        _run_step(9, "Constraints Override PO + Submit", step_delay_seconds, lambda: _submit_optimization_with_po(page))
        _run_step(10, "Assign to New Load", step_delay_seconds, lambda: _assign_to_new_load(page))
        _run_step(11, "Open Loads panel", step_delay_seconds, lambda: _open_loads_panel(page))
        _run_step(12, "Select load + Release Shipment Plan", step_delay_seconds, lambda: _select_load_and_release(page))
        _run_step(13, "Tender load", step_delay_seconds, lambda: _tender_load(page))
        _run_step(14, "Cleanup and logout", step_delay_seconds, lambda: _final_cleanup_and_logout(page))

        print("TMS process complete.")
        time.sleep(1)
        context.close()
        browser.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TMS Playwright automation (codegen-aligned).")
    parser.add_argument(
        "--step-delay-seconds",
        type=float,
        default=1.5,
        help="Pause between steps for visible execution (default: 1.5).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_tms_process(step_delay_seconds=max(0.0, args.step_delay_seconds))
