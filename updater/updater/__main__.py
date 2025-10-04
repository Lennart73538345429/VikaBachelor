from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path
from updater.updater.llm_support.gemini_client import gemini

# Schemata für die AI
schema = {
    "category": "Tierkategorie (z.B. Affen, Raubtiere, ...)",
    "latin": "Wissenschaftlicher Name",
    "russian": "Russischer Name",
    "gender_russian": "Genus im Russischen (M oder F)",
    "gender_german": "Genus im Deutschen (M, F oder N)"
}

example = {
    "input_example": (
        "Affen\n"
        "Latein       Russisch                     M/F  Deutsch\n"
        "Cercopithecus cephus  Голуболицая мартышка   F    F\n"
        "Ateles fusciceps rufiventris  Буроголовая коата   F    M"
    ),
    "output_example": [
        {
            "category": "Affen",
            "latin": "Cercopithecus cephus",
            "russian": "Голуболицая мартышка",
            "gender_russian": "F",
            "gender_german": "F"
        },
        {
            "category": "Affen",
            "latin": "Ateles fusciceps rufiventris",
            "russian": "Буроголовая коата",
            "gender_russian": "F",
            "gender_german": "M"
        }
    ]
}

# csv einlesen
def extract_rows(input_csv: Path) -> list[dict]:
    """
    Liest die Eingabe-CSV ein und erzeugt einfache Records (category aus Überschriftszeilen stammend).
    """
    data: list[dict] = []
    category: str | None = None

    with input_csv.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or all(not (c or "").strip() for c in row):
                continue

            first = (row[0] or "").strip()

            # Kategorie-Zeilen merken
            if first.endswith(":"):
                category = first.rstrip(":").strip()
                continue


            latin = (row[0] or "").strip() if len(row) > 0 else ""
            german = (row[1] or "").strip() if len(row) > 1 else ""
            russian = (row[2] or "").strip() if len(row) > 2 else ""

            if not (latin or german or russian):
                continue

            data.append({
                "category": category or "",
                "latin": latin,
                "german": german,
                "russian": russian
            })
    return data

def main():
    DEFAULT_CSV = Path("Neue DatenbankCSV.csv")

    parser = argparse.ArgumentParser(description="CSV einlesen, an LLM senden, Ergebnis zurückgeben")
    parser.add_argument("--csv", "-c", type=Path, default=DEFAULT_CSV,
                        help=f'Pfad zur Eingabe-CSV (Standard: "{DEFAULT_CSV}")')
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"FehlerCSV nicht gefunden: {args.csv.resolve()}", file=sys.stderr)
        sys.exit(1)

    # CSV
    try:
        payload = extract_rows(args.csv)
    except Exception as e:
        print(f"Fehler CSV: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = gemini.query_parsed(
            task="json_extraction",
            payload=payload,
            schema=schema,
            example=example
        )
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
    except Exception:
        pass


    try:
        raw = gemini.query_build(
            task="json_extraction",
            payload=payload,
            schema=schema,
            example=example
        )
        if isinstance(raw, (dict, list)):
            print(json.dumps(raw, ensure_ascii=False, indent=2))
        else:
            print(str(raw))
    except Exception as e:
        print(f"fehler: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
