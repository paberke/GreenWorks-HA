"""Fehlercodes des Optimow (RLM1) - Quelle der Texte fuer die Uebersetzungsdateien.

Englisch: aus der Greenworks-Connect-App (string_basefunction_mower_errorN).
Deutsch: Codes 13, 34, 47, 53, 59, 64 wie in der deutschen App-Fehlerliste,
die uebrigen sinngemaess uebersetzt.

Aufruf: python3 tools/error_codes.py  -> schreibt die Texte in strings.json
und translations/{de,en}.json.
"""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "error_texts",
    Path(__file__).resolve().parent.parent / "custom_components" / "greenworks" / "error_texts.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
ERRORS = _mod.ERRORS


def state_texts(lang: str) -> dict[str, str]:
    idx = 0 if lang == "en" else 1
    out = {f"e{code}": texts[idx] for code, texts in ERRORS.items()}
    out["unknown"] = "Unknown" if lang == "en" else "Unbekannt"
    return out


if __name__ == "__main__":
    import json
    from pathlib import Path

    base = Path(__file__).resolve().parent.parent / "custom_components" / "greenworks"
    for rel, lang in (("strings.json", "en"), ("translations/en.json", "en"), ("translations/de.json", "de")):
        path = base / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        sensors = data["entity"]["sensor"]
        texts = state_texts(lang)
        sensors["last_error"]["state_attributes"] = {
            "meaning": {"name": "Meaning" if lang == "en" else "Bedeutung", "state": texts}
        }
        sensors["last_error_text"] = {
            "name": "Last error message" if lang == "en" else "Letzte Fehlermeldung",
            "state": texts,
            "state_attributes": {
                "text": {"name": "Text" if lang == "en" else "Klartext"},
                "history": {"name": "History" if lang == "en" else "Verlauf"},
                "history_updated": {"name": "History updated" if lang == "en" else "Verlauf aktualisiert"},
            },
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("geschrieben:", rel)
