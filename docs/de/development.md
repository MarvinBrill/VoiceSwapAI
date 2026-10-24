# Lokale Entwicklung und Tests

[Übersicht](README.md) · [English](../en/development.md)

Für die normale Nutzung die Hardware-Anleitungen verwenden. Diese Anleitung richtet
sich an Änderungen an Backend und Oberfläche. Benötigt werden Python 3.12, Node.js
(hier mit Version 22 geprüft), npm sowie FFmpeg und FFprobe im PATH.

## Projektstruktur

| Ordner | Inhalt |
| --- | --- |
| `frontend/` | React, TypeScript, Vite |
| `backend/app/` | FastAPI, SQLite, Auftragsverarbeitung |
| `engine/rvc/` | Übernommener und angepasster RVC-Kern |
| `scripts/` | Windows-Launcher und Integrationstests |

Das benachbarte Original-RVC-Repository wird nicht benötigt. Herkunft:
[UPSTREAM.md](../../engine/UPSTREAM.md).

## Backend mit CUDA oder CPU

Im Projektordner eine getrennte Umgebung erstellen:

```sh
python -m venv .venv
```

Dabei muss `python` Python 3.12 sein. Unter Linux ggf. `python3.12` verwenden.
Ohne Aktivierung in den folgenden Befehlen jedes `python` durch
`.\.venv\Scripts\python.exe` (PowerShell) bzw. `.venv/bin/python` (Linux) ersetzen.
Alternativ unter Linux vorher `source .venv/bin/activate` ausführen.
Die Befehle müssen innerhalb dieser Umgebung ausgeführt werden:

```sh
python -m pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Für CPU im ersten Installationsbefehl `cu128` durch `cpu` ersetzen. Für einen expliziten
CPU-Start `VOICESWAP_DEVICE=cpu` setzen (PowerShell: `$env:VOICESWAP_DEVICE='cpu'`,
Linux: `export VOICESWAP_DEVICE=cpu`). Ohne Vorgabe erkennt die App verfügbare Geräte automatisch.

## Backend mit DirectML unter Windows

Zunächst `start-windows.cmd --check` für die Einrichtung ausführen. Danach in PowerShell:

```powershell
$env:VOICESWAP_DEVICE = 'directml'
$env:VOICESWAP_DIRECTML_DEVICE = '0'
.\.venv-directml\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

GPU-Nummer passend wählen. **Nicht** die CUDA-Pakete in `.venv-directml` installieren:
DirectML benötigt die getrennten Versionen aus `backend/requirements-directml.txt`.
FFmpeg/FFprobe müssen auch in diesem Terminal erreichbar sein; nach der Erstinstallation
ggf. ein neues Terminal öffnen.

## Oberfläche in einem zweiten Terminal

```sh
cd frontend
npm ci
npm run dev
```

http://localhost:5173 öffnen. Vite leitet `/api` an Port 8000 weiter. Nach dem Beenden
mit Strg+C erzeugt `npm run build` die Produktionsdateien in `frontend/dist/`.

## Prüfen

Im Projektordner, mit der ausgewählten Python-Umgebung und installierten Entwicklungsabhängigkeiten:

```sh
python -m pip install -r backend/requirements-dev.txt
python -m pytest
python -m ruff check backend scripts
```

Browser-Tests benötigen eine laufende Backend-App auf Port 8000 und ein gebautes Frontend:

```sh
cd frontend
npm run build
npx playwright install chromium
npm run test:e2e
```

Für andere Testadressen `APP_URL` setzen, z. B. in PowerShell
`$env:APP_URL='http://localhost:7860'`, unter Linux `export APP_URL=http://localhost:7860`.

Die Integrationstests `scripts/smoke.py` und `scripts/check_extended.py` trainieren
und konvertieren tatsächlich. Sie erzeugen Testaufnahmen, Projekte, Modelle und Ausgaben.
Nur gegen eine Testinstanz ausführen. Mit `VOICESWAP_DATA` vor dem Backend-Start einen
separaten Datenordner wählen; Basisgewichte werden dort ggf. erneut heruntergeladen.
Aufrufdetails stehen in der [Projekt-README](../../README.md).
