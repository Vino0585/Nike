
import sys
import json
import ast
import platform
import subprocess

def prompt_and_read_multiline() -> str:
    """
    Prompts the user and reads multi-line input until:
      - a blank line is entered, OR
      - EOF is reached (Ctrl+D on macOS/Linux, Ctrl+Z then Enter on Windows).
    Returns the combined text.
    """
    print("Paste your JSON (or dict-like text).")
    print("End with a blank line OR press Ctrl+D (macOS/Linux) / Ctrl+Z then Enter (Windows).")
    print("-------------------------------------------------------------")

    lines = []
    try:
        while True:
            line = input()
            # End on a blank line to avoid hanging for interactive users
            if line.strip() == "":
                break
            lines.append(line)
    except EOFError:
        pass

    text = "\n".join(lines).strip()
    if not text:
        print("No input captured. Please run again and paste your JSON.")
    return text

def try_parse_json_strict(text: str):
    """Try strict JSON parsing."""
    return json.loads(text)

def try_parse_fallback_python_literal(text: str):
    """
    Fallback: parse Python literal (e.g., {'a': 1} with single quotes)
    using ast.literal_eval. This is permissive, but not a replacement
    for valid JSON.
    """
    obj = ast.literal_eval(text)
    return obj

def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to clipboard with platform-aware strategy:
      - macOS (Darwin): use 'pbcopy' (most reliable)
      - Else: try pyperclip, then tkinter
    Returns True on success, False otherwise.
    """
    system = platform.system()

    # macOS: prefer pbcopy
    if system == "Darwin":
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-8"))
            if p.returncode == 0:
                return True
        except Exception:
            # Fall through to other methods
            pass

    # Try pyperclip if available
    try:
        import pyperclip  # type: ignore
        pyperclip.copy(text)
        return True
    except Exception:
        pass

    # Fallback to tkinter
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False

def format_json_with_trailing_commas_fix(text: str):
    """
    Optional minor cleanup for common issues:
      - Removes trailing commas in objects/arrays (best-effort).
    Conservative: only removes commas before closing ] or }.
    """
    import re
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text

def main():
    raw = prompt_and_read_multiline()
    if not raw:
        return

    parsed = None
    parse_mode = ""

    # Try strict JSON first
    try:
        parsed = try_parse_json_strict(raw)
        parse_mode = "strict JSON"
    except json.JSONDecodeError:
        # Try cleanup then strict JSON again
        cleaned = format_json_with_trailing_commas_fix(raw)
        try:
            parsed = try_parse_json_strict(cleaned)
            parse_mode = "strict JSON (after cleanup)"
        except json.JSONDecodeError:
            # Fallback to Python literal
            try:
                parsed = try_parse_fallback_python_literal(raw)
                parse_mode = "fallback (Python literal)"
            except Exception as e:
                print("❌ Unable to parse input as JSON or Python literal.")
                print("Error:", e)
                print("\nTips:")
                print('- Ensure keys/strings use double quotes: "key": "value"')
                print("- Remove trailing commas at the end of objects/arrays")
                print("- Validate with a JSON linter if unsure")
                return

    formatted = json.dumps(parsed, indent=4, ensure_ascii=False)
    print("\n✅ Parsed using:", parse_mode)
    print("----- Formatted JSON -----")
    print(formatted)
    print("--------------------------")

    if copy_to_clipboard(formatted):
        print("📋 Formatted JSON copied to clipboard.")
    else:
        print("⚠️ Clipboard copy failed.")
        print("   On macOS, ensure Terminal/iTerm has clipboard access;")
        print("   if running inside a remote/VM/headless session, clipboard may be unavailable.")

if __name__ == "__main__":
    main()
