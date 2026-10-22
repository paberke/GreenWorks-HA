"""Schreibt die Fehlerliste ERRORS.md (Englisch) und ERRORS.de.md (Deutsch).

Code und Bedeutung kommen aus custom_components/greenworks/error_texts.py (wie in
der Integration), die Tipps aus tools/error_tips.py.

Aufruf: python3 tools/error_list.py
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ERRORS = _load(ROOT / "custom_components" / "greenworks" / "error_texts.py", "error_texts").ERRORS
TIPS = _load(Path(__file__).resolve().parent / "error_tips.py", "error_tips").TIPS

HEAD = {
    "en": (
        "# Error codes\n\n"
        "**English** · [Deutsch](ERRORS.de.md) · [Back to the README](README.md)\n\n"
        "All {n} error codes the mower can report. The integration shows them in **Last error message**, "
        "in the **Problem** sensor and in the **Error** event.\n\n"
        "> [!NOTE]\n"
        "> The column **Meaning** comes from the Greenworks app. The column **What to do? (tip by Claude)** "
        "was written by **Claude (AI)** and is **not official Greenworks information**. "
        "If in doubt, ask Greenworks support or check the manual of your mower.\n\n"
        "| Code | Meaning | What to do? (tip by Claude) |\n|---:|---|---|\n"
    ),
    "de": (
        "# Fehlercodes\n\n"
        "[English](ERRORS.md) · **Deutsch** · [Zurück zur Readme](README.de.md)\n\n"
        "Alle {n} Fehlercodes, die der Mäher melden kann. Die Integration zeigt sie in **Letzte Fehlermeldung**, "
        "im Sensor **Problem** und im Ereignis **Fehler**.\n\n"
        "> [!NOTE]\n"
        "> Die Spalte **Bedeutung** stammt aus der Greenworks-App. Die Spalte **Was tun? (Tipp von Claude)** "
        "wurde von **Claude (KI)** geschrieben und ist **kein offizieller Text von Greenworks**. "
        "Im Zweifel bitte den Greenworks-Support fragen oder in die Anleitung des Mähers schauen.\n\n"
        "| Code | Bedeutung | Was tun? (Tipp von Claude) |\n|---:|---|---|\n"
    ),
}

FILES = {"en": "ERRORS.md", "de": "ERRORS.de.md"}


def build(lang: str) -> str:
    idx = 0 if lang == "en" else 1
    rows = [
        f"| {code} | {texts[idx]} | {TIPS[code][idx]} |"
        for code, texts in sorted(ERRORS.items())
    ]
    return HEAD[lang].format(n=len(ERRORS)) + "\n".join(rows) + "\n"


if __name__ == "__main__":
    missing = sorted(set(ERRORS) - set(TIPS))
    if missing:
        raise SystemExit(f"Tipps fehlen fuer: {missing}")
    for lang, name in FILES.items():
        (ROOT / name).write_text(build(lang), encoding="utf-8")
        print("geschrieben:", name)
