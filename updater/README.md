# Updater für Mitteldeutsche KI-Landkarte

## Key Handling
 - Um API Keys zu schützen lade sie niemals mit auf Github hoch, Nutze die erstelle eine `.env` Datei im `data_services/updater` Ordner und hinterlege den Schlüssel dort, diese wird von Github ignoriert. 
## Ausführen
Hinweis: Das Modul muss immer mit mindestens einer gültigen JSON-Datei ausgeführt werden. Pfade müssen relativ zum Projektverzeichnis angegeben werden.

- `python -m updater.updater updater/input.json`

## Build Docker Container

- `docker build -f updater/Dockerfile -t updater . `

## Ausführen mit Eingabe

- `docker run --rm updater updater/updater/testdata/extractorresultkupper.json`

# Ausführen ohne Eingabe führt zu keinem Ergebnis
- `docker run --rm updater`

## Gemini response codes
 - sollten keine Daten von Gemini zurück kommen, wird ein Statuscode ausgegeben. 

| HTTP Code | Status             | Description                                             |
|-----------|--------------------|---------------------------------------------------------|
| 404       | NOT_FOUND          | The requested resource wasn't found.                   |
| 429       | RESOURCE_EXHAUSTED | You've exceeded the rate limit.                        |
| 500       | INTERNAL           | An unexpected error occurred on Google's side.         |
| 503       | UNAVAILABLE        | The service may be temporarily overloaded or down.     |


### Tips
- eventuell Befehle mit `sudo`ausführen

