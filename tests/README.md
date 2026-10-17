# Tests

Automatische Tests der Integration mit nachgestellten Antworten der Greenworks-Cloud.
Die Beispieldaten in `fixtures/sample_mower.json` sind anonymisiert (keine Seriennummer,
keine SIM-Nummer, keine echte Position).

```bash
pip install pytest-homeassistant-custom-component
python -m pytest -q
```

Auf GitHub laufen die Tests bei jeder Änderung automatisch (siehe `.github/workflows/tests.yaml`).
