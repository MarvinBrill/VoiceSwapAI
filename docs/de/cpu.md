# CPU-Modus mit Docker

[Übersicht](README.md) · [English](../en/cpu.md)

Dieser Modus benötigt keine GPU-Freigabe. **Training und Stimmenersetzung rechnen auf
der CPU** und sind erheblich langsamer. CPU-Konvertierung wurde geprüft; ein vollständiges
CPU-Training wurde nicht durchgeführt.

## Voraussetzungen

- Windows x64 mit Docker Desktop im Linux-Container-Modus oder Linux x86-64 mit Docker Engine.
- Docker Compose mindestens 2.30 und der vollständige Projektordner.
- Internet für Installation/Basisgewichte, genügend RAM und freier Festplattenspeicher.

Für Apple Silicon/ARM64 ist dieser Stack nicht validiert; manche festgelegten Pakete
können dort fehlen. Mac-GPU-Beschleunigung über Metal/MPS ist nicht implementiert.

## Starten

Im Projektordner:

```sh
docker compose -f compose.yaml -f compose.cpu.yaml up --build -d
docker compose -f compose.yaml -f compose.cpu.yaml ps
```

http://localhost:7860 öffnen. Die App lädt fehlende Basisdateien automatisch.
Unter **System & Speicher** muss **CPU** stehen. Mit Batch 1 und kurzen eigenen
Audios beginnen; auch Gesangstrennung benötigt in diesem Modus CPU-Zeit.

## Stoppen und erneut starten

```sh
docker compose -f compose.yaml -f compose.cpu.yaml stop
docker compose -f compose.yaml -f compose.cpu.yaml up -d
```

Nach Änderungen am Projekt zum Start zusätzlich `--build` verwenden. Beide
`-f`-Dateien sind immer nötig, sonst wird die NVIDIA-Standardkonfiguration benutzt.

Protokolle:

```sh
docker compose -f compose.yaml -f compose.cpu.yaml logs --tail 100 voiceswap
```

Das Docker-Volume bleibt beim Stoppen erhalten. [Bedienung](usage.md) · [Wartung](maintenance.md).
