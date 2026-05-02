"""
Automates UDC landing login and navigation to Original Order via the app menu.

Credentials must NOT be stored in this file. Set environment variables:

  export UDC_USERNAME="your_username"
  export UDC_PASSWORD="your_password"

Optional:
  UDC_HEADLESS=1          Run browser headless (default: visible window)
  UDC_SLOW_MO_MS=200      Slow down actions for debugging (milliseconds)

Usage (from repo root or this directory):

  pip install -r J30/automation/requirements.txt
  playwright install chromium
  python J30/automation/udc_login_original_order.py
"""

from __future__ import annotations

import os
import re
import sys


LANDING_URL = "https://nikeaplawmqa1.sce.manh.com/udc/landing"
MENU_SEARCH_TERM = "Original Order"


def _env_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"Missing environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def _fill_login(page, username: str, password: str) -> None:
    """Try common Manhattan / SSO-style login field patterns."""
    candidates_user = [
        'input[name="username"]',
        'input[name="userName"]',
        'input[name="UserName"]',
        'input#username',
        'input[type="text"]',
        'input[autocomplete="username"]',
    ]
    candidates_pass = [
        'input[name="password"]',
        'input[name="Password"]',
        'input#password',
        'input[type="password"]',
    ]

    page.wait_for_load_state("networkidle", timeout=60_000)

    filled_user = False
    for sel in candidates_user:
        loc = page.locator(sel).first
        if loc.count() > 0:
            try:
                loc.wait_for(state="visible", timeout=5_000)
                loc.fill(username)
                filled_user = True
                break
            except Exception:
                continue
    if not filled_user:
        raise RuntimeError(
            "Could not find username field. Inspect the page and add a selector "
            "to candidates_user in udc_login_original_order.py."
        )

    filled_pass = False
    for sel in candidates_pass:
        loc = page.locator(sel).first
        if loc.count() > 0:
            try:
                loc.wait_for(state="visible", timeout=5_000)
                loc.fill(password)
                filled_pass = True
                break
            except Exception:
                continue
    if not filled_pass:
        raise RuntimeError(
            "Could not find password field. Inspect the page and add a selector "
            "to candidates_pass in udc_login_original_order.py."
        )

    login_clicked = False
    for role_name in ("Login", "Sign in", "Log in"):
        btn = page.get_by_role("button", name=re.compile(f"^{re.escape(role_name)}$", re.I))
        if btn.count():
            btn.first.click()
            login_clicked = True
            break
    if not login_clicked:
        submit = page.locator('button[type="submit"], input[type="submit"]').first
        if submit.count():
            submit.click()
            login_clicked = True
    if not login_clicked:
        raise RuntimeError(
            "Could not find login button. Inspect the page and extend login click logic."
        )


def _open_menu_and_go_original_order(page) -> None:
    """Hamburger → search 'Original Order' → select result."""
    page.wait_for_load_state("networkidle", timeout=90_000)

    menu_patterns = [
        page.get_by_role("button", name=re.compile(r"menu", re.I)),
        page.locator('[aria-label*="menu" i]'),
        page.locator('[aria-label*="navigation" i]'),
        page.locator("button.mat-mdc-menu-trigger"),
        page.locator(".hamburger"),
        page.locator('[data-testid*="menu" i]'),
    ]
    opened = False
    for loc in menu_patterns:
        try:
            candidate = loc.first
            if candidate.count() == 0:
                continue
            candidate.wait_for(state="visible", timeout=8_000)
            candidate.click()
            opened = True
            break
        except Exception:
            continue
    if not opened:
        raise RuntimeError(
            "Could not find hamburger / menu button. Add a stable selector for your build."
        )

    page.wait_for_timeout(500)

    search_selectors = [
        'input[type="search"]',
        'input[placeholder*="Search" i]',
        'input[aria-label*="Search" i]',
        'input.mat-input-element',
        'input[type="text"]',
    ]
    search_input = None
    for sel in search_selectors:
        box = page.locator(sel).filter(has_not=page.locator('[type="password"]')).first
        try:
            if box.count() and box.is_visible():
                search_input = box
                break
        except Exception:
            continue
    if search_input is None:
        raise RuntimeError(
            "Could not find menu search input. Inspect drawer/panel and add a selector."
        )

    search_input.fill(MENU_SEARCH_TERM)
    page.keyboard.press("Enter")
    page.wait_for_timeout(750)

    link_or_row = page.get_by_role("menuitem", name=re.compile(r"Original\s+Order", re.I))
    if link_or_row.count():
        link_or_row.first.click()
        return

    option = page.get_by_role("option", name=re.compile(r"Original\s+Order", re.I))
    if option.count():
        option.first.click()
        return

    cell_or_link = page.get_by_text(re.compile(r"^\s*Original\s+Order\s*$", re.I))
    if cell_or_link.count():
        cell_or_link.first.click()
        return

    raise RuntimeError(
        "Could not click 'Original Order' in results. Inspect list markup and adjust selectors."
    )


def main() -> None:
    from playwright.sync_api import sync_playwright

    username = _env_required("UDC_USERNAME")
    password = _env_required("UDC_PASSWORD")
    headless = os.environ.get("UDC_HEADLESS", "").strip() in ("1", "true", "yes")
    slow_mo = int(os.environ.get("UDC_SLOW_MO_MS", "0") or "0")

    launch_kw: dict = {"headless": headless}
    if slow_mo > 0:
        launch_kw["slow_mo"] = slow_mo

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kw)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.set_default_timeout(60_000)

        page.goto(LANDING_URL, wait_until="domcontentloaded")
        _fill_login(page, username, password)
        _open_menu_and_go_original_order(page)

        print("Login and navigation to Original Order completed (no post-login assertion run).")
        if not headless:
            input("Press Enter to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
