from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Iterable, Tuple
from updater.updater.llm_support.gemini_client import gemini



schema: Dict[str, str] = {
    "category": "Tierkategorie (z.B. Affen, Raubtiere, ...)",
    "latin": "Wissenschaftlicher Name",
    "russian": "Russischer Name",
    "gender_russian": "Genus im Russischen (M oder F)",
    "gender_german": "Genus im Deutschen (M, F oder N)"
}

example: Dict[str, Any] = {
    "input_example": (
        "Affen\n"
        "Latein       Russisch                     M/F  Deutsch\n"
        "Cercopithecus cephus  Голуболицая мартышка   F    F\n"
        "Ateles fusciceps rufiventris  Буроголовая коата   F    M"
    ),
    "output_example": [
        {
            "category": "Affen",
            "latin": "Pan troglodytes",
            "german": "Schimpanse",
            "russian": "Обыкновенный шимпанзе",
            "gender_russian": "M",
            "gender_german": "M",
            "score": 0.95,
            "reason": "Schimpansen teilen etwa 98,8 % ihrer DNA mit dem Menschen, zeigen komplexe soziale Strukturen, Werkzeuggebrauch und kognitive Fähigkeiten.",
            "gender_reason": "Genusregel: Maskulin, da 'Schimpanse' im Deutschen maskulin ist."
        }
    ]
}


def extract_rows(input_csv: Path) -> List[Dict[str, str]]:
    """
    Liest die Eingabe-CSV ein und erzeugt Records.
    Erwartete Spalten (flexibel): latin, german, russian (in dieser Reihenfolge).
    Kategorieschilder werden aus Zeilen mit ':' am Ende entnommen.
    """
    data: List[Dict[str, str]] = []
    category: str | None = None

    with input_csv.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or all(not (c or "").strip() for c in row):
                continue

            first = (row[0] or "").strip()

            
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


def chunk(lst: List[Any], n: int) -> Iterable[List[Any]]:
    for i in range(0, len(lst), n):
        yield lst[i:i+n]


def extract_json_array(s: str) -> List[Any]:
    """
    Robuste Extraktion: versucht erst json.loads(s),
    fällt dann auf das größte balancierte JSON-Array [] zurück.
    """
   
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return parsed
        # falls ein Objekt mit items zurückkommt
        if isinstance(parsed, dict):
            items = parsed.get("items")
            if isinstance(items, list):
                return items
        
            for k, v in parsed.items():
                if isinstance(v, list):
                    return v
      
    except Exception:
        pass

 
    best_candidate: List[Any] | None = None
    best_len = -1
    stack = []
    start_idx = None

    for i, ch in enumerate(s):
        if ch == '[':
            stack.append('[')
            if len(stack) == 1:
                start_idx = i
        elif ch == ']':
            if stack:
                stack.pop()
                if not stack and start_idx is not None:
                    candidate_str = s[start_idx:i + 1]
                    try:
                        arr = json.loads(candidate_str)
                        if isinstance(arr, list):
                            if len(candidate_str) > best_len:
                                best_len = len(candidate_str)
                                best_candidate = arr
                    except Exception:
                        pass
                    start_idx = None

    if best_candidate is not None:
        return best_candidate

    raise ValueError("Konnte kein JSON-Array extrahieren")


def record_key(r: Dict[str, Any]) -> Tuple[str, str, str]:
    """Eindeutiger Key zur Duplikat-/Vollständigkeitsprüfung."""
    return (
        (r.get("latin") or "").strip(),
        (r.get("russian") or "").strip(),
        (r.get("german") or "").strip()
    )


def call_model_batch(batch_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Führt den LLM-Call für einen Batch aus – erst parsed, dann robustes Fallback.
    Gibt immer eine Liste von Objekten zurück (leer, wenn nichts geparst werden konnte).
    """

    try:
        part = gemini.query_parsed(
            task="json_extraction",
            payload=batch_payload,
            schema=schema,
            example=example
        )
        if isinstance(part, list):
            return part
        if isinstance(part, dict):
            # häufiges Muster: { "items": [...] }
            items = part.get("items")
            if isinstance(items, list):
                return items
    except Exception:
        pass

    
    try:
        raw = gemini.query_build(
            task="json_extraction",
            payload=batch_payload,
            schema=schema,
            example=example
        )
        if isinstance(raw, (list, dict)):
           
            if isinstance(raw, list):
                return raw
            # dict -> best effort
            items = raw.get("items")
            return items if isinstance(items, list) else []
        # ansonsten String -> extrahieren
        return extract_json_array(str(raw))
    except Exception:
        return []




def main():
    # Standard-Dateien: beide Tabellen
    DEFAULT_CSV_1 = Path("Neue DatenbankCSV.csv")
    DEFAULT_CSV_2 = Path("Neue DatenbankCSV1.csv")

    parser = argparse.ArgumentParser(
        description="CSV einlesen, in Batches an LLM senden, Ergebnisse zusammenführen"
    )
    parser.add_argument("--csv", "-c", type=Path, default=DEFAULT_CSV_1,
                        help=f'Pfad zur ersten Eingabe-CSV (Standard: "{DEFAULT_CSV_1}")')
    parser.add_argument("--csv2", "-c2", type=Path, default=DEFAULT_CSV_2,
                        help=f'Pfad zur zweiten Eingabe-CSV (Standard: "{DEFAULT_CSV_2}")')
    parser.add_argument("--batch-size", "-b", type=int, default=20,
                        help="Anzahl der Einträge pro LLM-Call (Standard: 20)")

    parser.add_argument("--max-retries", "-r", type=int, default=1,
                        help="Anzahl der Retry-Runden bei fehlenden Einträgen (Standard: 1)")
    parser.add_argument("--print-json", action="store_true",
                        help="Gesamtergebnis zusätzlich auf STDOUT ausgeben")
    args = parser.parse_args()

    # check files 
    if not args.csv.exists():
        print(f"Fehler: CSV nicht gefunden: {args.csv.resolve()}", file=sys.stderr)
        sys.exit(1)
    if not args.csv2.exists():
        print(f"Fehler: CSV nicht gefunden: {args.csv2.resolve()}", file=sys.stderr)
        sys.exit(1)

    # join csv files
    try:
        payload1 = extract_rows(args.csv)
        print(f"Erste CSV mit {len(payload1)} Zeilen eingelesen.", file=sys.stderr)
        payload2 = extract_rows(args.csv2)
        print(f"Zweite CSV mit {len(payload2)} Zeilen eingelesen.", file=sys.stderr)
        payload = payload1 + payload2
        print(f"Gesamt {len(payload)} Zeilen ", file=sys.stderr)
    except Exception as e:
        print(f"Fehler : {e}", file=sys.stderr)
        sys.exit(1)
        
    all_results: List[Dict[str, Any]] = []
    for i, batch in enumerate(chunk(payload, args.batch_size), start=1):
        part = call_model_batch(batch)
        if not isinstance(part, list):
            part = []
        all_results.extend(part)
        print(f"Batch {i}: {len(part)} Elemente", file=sys.stderr)

    expected = len(payload)
    got_keys = {record_key(r) for r in all_results if isinstance(r, dict)}
    missing = [row for row in payload if record_key(row) not in got_keys]

    retry_round = 0
    while missing and retry_round < args.max_retries:
        retry_round += 1
        print(f"Retry {retry_round}: {len(missing)} – erneut",
              file=sys.stderr)

        new_results: List[Dict[str, Any]] = []
        for batch in chunk(missing, max(10, args.batch_size // 2)):  
            part = call_model_batch(batch)
            if isinstance(part, list):
                new_results.extend(part)

        for r in new_results:
            k = record_key(r) if isinstance(r, dict) else ("", "", "")
            if k and k not in got_keys:
                got_keys.add(k)
                all_results.append(r)

        missing = [row for row in payload if record_key(row) not in got_keys]
        print(f"Nach Retry {retry_round}: gesamt {len(all_results)} / erwartet {expected}",
              file=sys.stderr)
    # write to file
    out_path = Path("gemini_output.json")
    try:
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"Ergebnis unter: {out_path.resolve()}", file=sys.stderr)
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)

    if args.print_json:
    
        print(json.dumps(all_results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
