# VoiceSwapAI

**Anleitungen / Guides:** [Deutsch](docs/de/README.md) · [English](docs/en/README.md)

Die Anleitungen enthalten getrennte Installations- und Startschritte für CUDA,
Windows DirectML, Linux ROCm, Intel XPU und CPU sowie Betrieb und Entwicklung.

Ein lokales Voice Studio mit React-Oberfläche: Stimmen und Gesang mit eigenen
RVC-Modellen ersetzen, Voice-Modelle aus lokalen Aufnahmen trainieren und Ergebnisse
direkt vorhören und herunterladen. Dunkles Glasdesign, ohne Konto oder Cloud-Verarbeitung.

## Start mit NVIDIA-GPU

Docker Desktop mit WSL2/Linux-Containern und GPU-Unterstützung sowie einen aktuellen
NVIDIA-Treiber installieren. Im Repository starten:

```sh
docker compose up --build -d
```

**App öffnen: http://localhost:7860**

Die Standardkonfiguration nutzt NVIDIA CUDA, einschließlich RTX 50 / Blackwell.
Der Build installiert PyTorch **2.7.1 mit CUDA 12.8**, passend zum übernommenen RVC-Kern.
Ein lokales CUDA Toolkit ist nicht erforderlich. Für die Compose-Anleitungen
Docker Compose 2.30 oder neuer verwenden (`gpus: all` und `!reset` werden benötigt).

Beim ersten Start lädt die App ca. **1 GB RVC-Basisgewichte** automatisch herunter:
HuBERT, RMVPE und Generator-/Discriminator-Gewichte für 32/40/48 kHz. Fortschritt unter
**Ergebnisse**, Bereitschaft unter **System & Speicher**. Der erste Song-Auftrag lädt
zusätzlich das offizielle Hybrid-Demucs-Modell. Der Container samt CUDA benötigt mehrere
GB; für Build, Modelle und Trainings-Checkpoints ausreichend freien Speicher vorsehen
(etwa 20 GB als Ausgangspunkt, bei größeren Datensätzen mehr).

Internet ist für Installation und erstmalige Modelldownloads erforderlich. Danach
laufen vorbereitete Methoden offline. Aufnahmen und importierte Stimmen verlassen
den Rechner nicht; Schriftarten werden ebenfalls lokal ausgeliefert.

```sh
docker compose logs -f voiceswap
docker compose down
```

`down` erhält deine Daten. **`down -v` löscht das Datenvolume einschließlich deiner
Aufnahmen, Modelle und Ergebnisse.**

## Die Arbeitsabläufe

### Stimmen ersetzen

1. Unter **Modellbibliothek** eine oder mehrere exportierte RVC-v1/v2-`.pth`-Dateien
   hinzufügen. Optional den zugehörigen `.index` verbinden. Modelle werden dauerhaft
   gespeichert und sind nach einem Neustart wieder auswählbar.
2. Im **Voice Studio** lokale Audiodateien hochladen oder aus der Bibliothek wählen.
3. Voice-Modell auswählen. **Stimme pur** für Sprache/isolierten Gesang oder
   **Kompletter Song** für Gesangstrennung mit erhaltener Begleitung wählen.
4. Tonhöhe, Indexstärke, Konsonantenschutz, Lautstärkeverlauf und gegebenenfalls
   Gesangs-/Begleitungspegel einstellen. RMVPE, FCPE oder Parselmouth sind verfügbar.
5. Als WAV/FLAC (24 Bit) oder MP3 (320 kbit/s) exportieren. Ergebnisse erscheinen
   mit Audioplayer und Download. Bei Song-Verarbeitung gibt es zusätzliche
   Downloads für neue Stimme und Begleitung.

Die Bibliothek akzeptiert **exportierte RVC-Inferenzmodelle**, keine beliebigen
PyTorch-Netze, TTS-Modelle oder rohen `G_*.pth`-Trainings-Checkpoints.
Benutzermodelle werden ausschließlich mit PyTorch `weights_only=True` gelesen.

### Eigene Stimme trainieren

1. Unter **Training** ein Projekt benennen und lokale Audiodateien hinzufügen.
   Dateien sind einzeln vorhörbar, durchsuchbar und aus dem Datensatz entfernbar.
2. Samplerate, Epochen und Batch-Größe wählen. Für eine RTX 5070 Ti mit 16 GB VRAM
   ist Batch 4 ein Ausgangspunkt; bei Speichermangel 2 oder 1 verwenden.
3. Training starten. Die App bereitet Audio vor, extrahiert HuBERT- und Pitch-Merkmale,
   trainiert RVC v2 und erstellt einen FAISS-Stimmenindex.
4. Das Ergebnis wird automatisch zur Modellbibliothek hinzugefügt. `.pth` und `.index`
   lassen sich dort herunterladen und direkt verwenden.

Es werden ausschließlich die von dir im Browser hinzugefügten Audiodateien als
Trainingsdaten verwendet. Vortrainierte Basisgewichte dienen als Ausgangspunkt.
Saubere Sprache oder Gesang einer einzigen Stimme ohne Musik/Hall liefert bessere
Ergebnisse. Mehrere Minuten abwechslungsreiche Aufnahmen sind sinnvoll; circa zehn
Minuten sind ein guter Anfang. Sehr kurze Clips funktionieren ebenfalls, aber ein
kurzer technischer Test sagt nichts über die Qualität eines trainierten Modells aus.

Es gibt **keine feste Begrenzung für Dateianzahl oder Audiodauer**. Uploads werden
einzeln übertragen; Konvertierung erfolgt in 30-Sekunden-Abschnitten mit Kontext,
Training aus kurzen Abschnitten. Speicherplatz, RAM und Laufzeit bleiben praktische
Grenzen. Der Stimmenindex nutzt höchstens 200.000 zufällig ausgewählte Merkmale,
während das Training den vollständigen aufbereiteten Datensatz verwendet.

Aufträge laufen nacheinander, damit Training und Konvertierung nicht um VRAM konkurrieren.
Abbrechen beendet auch Unterprozesse. Nach einem Neustart werden unterbrochene Aufträge
markiert. Unter **Ergebnisse → Training fortsetzen** kann ein gespeicherter Trainingslauf
mit höherer Gesamtepochenzahl fortgesetzt werden. Dafür muss mindestens ein vollständiger
Generator-/Discriminator-Checkpoint existieren. Die ursprünglichen Trainingsdaten und
Architektureinstellungen werden dabei wiederverwendet.

## Andere Hardware

| Hardware | Startbefehl | Einschränkung |
| --- | --- | --- |
| NVIDIA RTX, einschließlich RTX 50 | `docker compose up --build -d` | NVIDIA-GPU-Freigabe in Docker erforderlich |
| CPU / beliebiger Rechner | `docker compose -f compose.yaml -f compose.cpu.yaml up --build -d` | Deutlich langsamer |
| AMD/Intel/NVIDIA unter Windows mit DirectX 12 | `start-windows.cmd` | Nativer DirectML-Start, ohne Docker; siehe unten |
| AMD ROCm unter Linux | `docker compose -f compose.yaml -f compose.amd.yaml up --build -d` | Unterstützte ROCm-6.3-GPU und Host-Treiber nötig; hier nicht hardwaregetestet |
| Intel XPU unter Linux | `docker compose -f compose.yaml -f compose.intel.yaml up --build -d` | Experimentell; passende Intel-Treiber und GPU erforderlich; hier nicht hardwaregetestet |

Bei AMD/Intel müssen `VIDEO_GID` und `RENDER_GID` gegebenenfalls in einer `.env` auf
die Gruppen-IDs des Hosts gesetzt werden (`getent group video render`).
Die zusätzlichen Konfigurationen verwenden dieselbe Bibliothek und denselben Port.
Zum Backendwechsel den bestehenden Container zuerst stoppen und dann die gewünschte
Konfiguration bauen/starten. Mac-GPUs und DirectML werden nicht durch Linux-Docker
weitergereicht. Für Windows gibt es deshalb zusätzlich den nativen DirectML-Start;
der CPU-Modus bleibt als Alternative verfügbar.

**Vulkan ist kein universeller Trainingsbackend für diese RVC-/PyTorch-Pipeline.**
VoiceSwapAI nutzt deshalb die Compute-Backends CUDA/ROCm/XPU und Windows DirectML
und bietet CPU als gemeinsame Rückfallebene. Es wird keine GPU-Unterstützung angezeigt,
wenn das konfigurierte Gerät nicht verfügbar ist.

### Windows mit AMD-GPU, einschließlich RX 6750 XT

Der zusätzliche **native DirectML-Start** verwendet DirectX 12 statt ROCm. Er ist
für Windows 10/11 x64 mit aktuellem Grafiktreiber und DirectX-12-fähiger GPU gedacht,
auch für AMD-Karten außerhalb der ROCm-Liste. Eine Garantie für jede Kombination aus
GPU und Treiber ist damit nicht verbunden. Ein Test auf einer RX 6750 XT steht noch aus.

Im entpackten/geklonten Repository `start-windows.cmd` doppelklicken oder in PowerShell:

```powershell
.\start-windows.cmd
```

Beim ersten Start werden bei Bedarf uv, Node.js LTS und FFmpeg über WinGet installiert.
uv richtet Python 3.12 und eine separate Umgebung `.venv-directml` ein; anschließend
werden Abhängigkeiten installiert und die Weboberfläche gebaut. WinGet (Windows
App-Installer) und Internetzugriff müssen vorhanden sein. Eventuelle Windows-Dialoge
für die Installation der Komponenten bestätigen. Es wird keine Sicherheitsrichtlinie geändert.
Spätere Starts verwenden die vorhandene Installation; geänderte Anforderungen und
Frontend-Dateien werden automatisch neu verarbeitet.

Ein kurzer Test prüft echte GPU-Berechnung, Trainingsgradienten und Checkpoints.
Danach öffnet sich `http://localhost:7860`. Das Terminal bleibt während der Nutzung
offen; **Strg+C** beendet die App. Docker wird für diesen Start nicht benötigt.
Aufnahmen, Modelle, Basisgewichte und Ergebnisse liegen in **`data/` im Repository**.
Der native Datenspeicher und ein vorhandenes Docker-Volume sind getrennt.

```powershell
# Verfügbare Grafikkarten anzeigen:
.\start-windows.cmd --list-devices
# Eine bestimmte GPU verwenden (Nummer aus der Liste):
.\start-windows.cmd --device 0
# Nur den GPU-Test ausführen:
.\start-windows.cmd --device 0 --check
# Falls bereits eine andere App auf Port 7860 läuft:
.\start-windows.cmd --port 7861
```

Bei mehreren GPUs die gewünschte Radeon anhand der Liste auswählen. Ohne Auswahl
wird der DirectML-Standardadapter verwendet. Das gewählte Gerät erscheint unter
**System & Speicher**; ein fehlendes Gerät führt zu einer Fehlermeldung, nicht zu
einem stillen CPU-Start. Für die RX 6750 XT zunächst Batch 1 und 40 kHz verwenden.

Generator, Discriminator, HuBERT und die großen Pitch-Netze rechnen auf DirectML
in FP32. Spektralanalyse, die RMVPE-GRU und einzelne nicht unterstützte Operatoren
verwenden CPU-Berechnungen, ebenso das Umordnen relativer Attention-Positionen.
Der Mel-Loss bleibt dabei mit dem GPU-Trainingsgraphen
verbunden. **Demucs-Gesangstrennung läuft in dieser Variante auf der CPU**; das
anschließende Ersetzen der Stimme läuft auf der GPU. Deshalb sind Laufzeit und
Speicherbedarf nicht direkt mit CUDA vergleichbar.

Microsofts `torch-directml==0.2.5.dev240914` benötigt PyTorch 2.4.1; diese Umgebung ist
vom CUDA-Docker-Setup mit PyTorch 2.7.1 getrennt. Die Versionsanzeige `2.4.1+cpu` ist
bei DirectML normal: Die Beschleunigung kommt vom separaten DirectML-Plugin.
Benutzermodelle müssen PyTorch-ZIP-Gewichte sein: Legacy-Pickle/TAR und TorchScript
werden vor dem Laden abgewiesen; der Loader bleibt auf `weights_only=True` beschränkt.
Vulkan ist weiterhin kein implementierter Trainingsbackend.

Quellen: [Microsoft DirectML / PyTorch](https://learn.microsoft.com/en-us/windows/ai/directml/pytorch-windows),
[DirectML-Paket](https://pypi.org/project/torch-directml/),
[Docker Desktop GPU-Unterstützung](https://docs.docker.com/desktop/features/gpu/).

## Daten und Betrieb

Bei Docker liegen die App-Daten im Volume `voiceswapai_voiceswap-data` unter `/data`.
Beim nativen Windows-Start liegen sie standardmäßig im Repository-Ordner `data/`.
Beide Speicherorte verwenden diese Struktur:

```text
/data/
  library.sqlite3   Metadaten, Projekte und Warteschlange
  uploads/          Originalaufnahmen
  models/           Importierte und trainierte Modelle / Indices
  assets/           Verifizierte Basisgewichte und Modell-Caches
  training/         Datensätze, Merkmale, Logs und Checkpoints
  jobs/             Prozessprotokolle
  outputs/          Konvertierte Audios und Stems
```

Für ein Backup zuerst den Container stoppen und das gesamte Volume sichern. Nur
die SQLite-Datei zu kopieren reicht nicht aus. Die App ist standardmäßig nur über
`127.0.0.1:7860` erreichbar und hat keine Benutzeranmeldung. Eine öffentliche
Bereitstellung ist nicht Bestandteil dieses Setups.

Optional in `.env`: `VOICESWAP_PORT=7861` für einen anderen Host-Port.

## Entwicklung und Tests

Der tatsächlich geprüfte Funktionsumfang und die verwendete Hardware stehen im
[Prüfprotokoll](docs/VERIFICATION.md).

Aufbau: `frontend/` React/TypeScript/Vite, `backend/app/` FastAPI, SQLite und
Prozess-Warteschlange, `engine/rvc/` ausgewählte RVC-Module. Herkunft und Anpassungen:
[engine/UPSTREAM.md](engine/UPSTREAM.md). Das benachbarte Originalrepository wird
für Build oder Laufzeit nicht benötigt.

Für lokale Backend-Entwicklung Python 3.12 und FFmpeg/FFprobe im PATH verwenden:

```sh
python -m venv .venv
# Virtuelle Umgebung aktivieren, dann:
pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python -m uvicorn app.main:app --app-dir backend --port 8000
```

```sh
cd frontend
npm ci
npm run dev
npm run build
```

Der Vite-Server unter `localhost:5173` leitet `/api` an Port 8000 weiter.

```sh
python -m pytest
ruff check backend scripts
cd frontend
npx playwright install chromium
npm run test:e2e
```

Der Browser-Test erwartet die gebaute App unter Port 8000 (`APP_URL` anpassbar).
Ein vollständiger GPU-Test trainiert mit lokal synthetisiertem Testaudio eine Epoche,
exportiert/reimportiert `.pth` und `.index`, konvertiert Audio und prüft die Ausgaben:

```sh
python scripts/smoke.py --url http://localhost:7860
# Optional auch Gesangstrennung testen:
python scripts/smoke.py --url http://localhost:7860 --separate
# Danach zusätzlich Fortsetzen, Abbrechen, 40-Sekunden-Audio, FCPE/FLAC und PM/MP3:
python scripts/check_extended.py --url http://localhost:7860
```

Testmodelle und Ergebnisse bleiben ausdrücklich als **Smoke-Test** markiert in der App.
Das ist ein Funktionstest, keine Aussage über die Stimmqualität.

## Technische Grundlagen

- [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI): Voice Conversion und Training.
- [PyTorch 2.7 / Blackwell](https://pytorch.org/blog/pytorch-2-7/): CUDA-12.8-Unterstützung.
- [Offizielle Basisgewichte](https://huggingface.co/lj1995/VoiceConversionWebUI): per Revision und SHA-256 festgelegt.
- [Hybrid Demucs](https://github.com/facebookresearch/demucs): Gesangstrennung bei vollständigen Songs.
- [Intel XPU](https://docs.pytorch.org/get-started/additional-platforms/): alternativer GPU-Backend.

VoiceSwapAI implementiert die wesentlichen lokalen Voice-Conversion-Arbeitsabläufe
eines Replay-artigen Studios. Eine pixelgenaue Kopie oder vollständige
Funktionsgleichheit mit einer früheren Replay-Version wird nicht vorausgesetzt.
