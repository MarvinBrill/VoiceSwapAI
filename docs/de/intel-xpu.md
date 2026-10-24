# Intel unter Linux / XPU mit Docker

[Übersicht](README.md) · [English](../en/intel-xpu.md)

**Experimentell und nicht hardwaregetestet.** Diese Variante verwendet `Dockerfile.intel`,
Intel-GPU-Bibliotheken im Container und PyTorch/torchaudio 2.7.1 mit XPU.
Unter Windows ist der separate [DirectML-Start](windows-directml.md) vorgesehen.

## Voraussetzungen

- Nativer Linux-x86-64-Host mit Docker Engine und Compose mindestens 2.30.
- Eine von der verwendeten PyTorch-XPU-/Intel-Treiberversion unterstützte Intel-GPU.
- Passender Host-Kernel/Grafiktreiber; Render-Geräte unter `/dev/dri`.
- Internetzugriff auch auf Intels Paketserver beim Build.

Die Treiberinstallation im Container ersetzt nicht den Host-Treiber. Die aktuelle
[PyTorch-XPU-Dokumentation](https://docs.pytorch.org/docs/stable/notes/get_start_xpu.html)
beschreibt die Plattform; eine Freigabe neuer Versionen gilt nicht automatisch für
das hier festgelegte PyTorch 2.7.1. Das Intel-Image wurde hier nicht gebaut oder ausgeführt.

## Gerätegruppen prüfen

```sh
ls -l /dev/dri/render*
getent group video render
```

Im Projektordner `.env` erstellen oder ergänzen. Die IDs der eigenen Gerätegruppen
verwenden; diese Zahlen sind nur Beispiele:

```dotenv
VIDEO_GID=44
RENDER_GID=109
```

## Starten und prüfen

```sh
docker compose -f compose.yaml -f compose.intel.yaml up --build -d
docker compose -f compose.yaml -f compose.intel.yaml ps
docker compose -f compose.yaml -f compose.intel.yaml exec voiceswap python -c "from app.devices import device_info; print(device_info())"
```

http://localhost:7860 öffnen. Unter **System & Speicher** müssen das Intel-Gerät
und **Intel XPU** erscheinen. Nach dem Basisdownload mit Batch 1 und kurzen eigenen
Aufnahmen prüfen, ob Training und Konvertierung auf dem Zielgerät funktionieren.
Noch nicht von zuverlässigem Betrieb ausgehen, wenn lediglich die GPU erkannt wurde.

## Stoppen und Fehler suchen

```sh
docker compose -f compose.yaml -f compose.intel.yaml stop
docker compose -f compose.yaml -f compose.intel.yaml logs --tail 100 voiceswap
```

Für Updates und Neustarts denselben Startbefehl mit beiden `-f`-Dateien verwenden.
Bei Zugriffsfehlern Render-Gruppen prüfen. Bei Buildfehlern Intel-Paketquelle und
Paketverfügbarkeit prüfen; bei XPU-Fehlern Host-Treiber und GPU-Kompatibilität.
Als Alternative steht [CPU](cpu.md) zur Verfügung.

[Bedienung](usage.md) · [Sicherung und Backendwechsel](maintenance.md).
