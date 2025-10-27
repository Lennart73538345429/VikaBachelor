# Data Services für Mitteldeutsche KI-Landkarte

## Installation

- Python 3.12
- `pip install -r requirements.txt`
 
Crawler:
- `python crawler/crawler`

Extractor:
- `python extractor/extractor`

Updater:
- siehe [updater/README.md](updater/README.md)

## Entwicklung

- Empfohlene IDE: [PyCharm](https://www.jetbrains.com/pycharm/)
- Einrichtung der Git Hooks

```sh
git config --local core.hooksPath .githooks/
chmod +x .githooks/*
```

- Linter:
  - `ruff check .`
- Formatter:
  - `ruff format .`
  
##Ausführen
  python3 -m updater.updater   --csv  "updater/updater/Neue DatenbankCSV.csv"   --csv2 "updater/updater/Neue DatenbankCSV1.csv"

-208 Zeilen erwartet

## Hilfreiche Links

- [Python Dokumentation](https://docs.python.org/3.12/)

## LLM Hinweise
 - API Keys sollten in einer .env benannten Datei im data_services Verzeichnis abgelegt werden.
 - Format der API Keys: `Key_Name=123456789`
