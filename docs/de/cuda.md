# NVIDIA / CUDA mit Docker

[Übersicht](README.md) · [English](../en/cuda.md)

## Voraussetzungen

- Windows x64 mit Docker Desktop und WSL2/Linux-Containern oder Linux x86-64 mit Docker Engine.
- NVIDIA-GPU mit passendem aktuellem Treiber. RTX 50 / Blackwell wird durch
  PyTorch 2.7.1 mit CUDA 12.8 berücksichtigt; RTX 5070 Ti wurde tatsächlich getestet.
- Docker Compose mindestens 2.30 für `gpus: all`.
- Vollständiger Projektordner, Internet für den ersten Build und genügend Speicherplatz.

Ein separat installiertes CUDA Toolkit auf dem Host ist nicht nötig.

### Windows vorbereiten

NVIDIA-Treiber und Docker Desktop installieren. In Docker Desktop den WSL2-Backend
und Linux-Container verwenden. Docker muss laufen. Bei veraltetem WSL in PowerShell:

```powershell
wsl --update
```

Danach Docker Desktop ggf. neu starten. Siehe [Docker: GPU unter Windows](https://docs.docker.com/desktop/features/gpu/).

### Linux vorbereiten

NVIDIA-Treiber, Docker Engine mit Compose-Plugin und das
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
nach der Anleitung für die eigene Distribution installieren und für Docker konfigurieren.
`nvidia-smi` muss auf dem Host die GPU erkennen. Ein funktionierender Host-Treiber allein
reicht ohne GPU-Freigabe an Docker nicht aus.

## Starten

Im Projektordner, in PowerShell oder einem Linux-Terminal:

```sh
docker compose up --build -d
docker compose ps
```

http://localhost:7860 öffnen. Der erste Start lädt fehlende Basisgewichte automatisch.
Unter **System & Speicher** müssen die gewünschte NVIDIA-GPU und **CUDA** erscheinen.
Training und Stimmenersetzung verwenden die GPU; Audio-I/O und einzelne Hilfsschritte verwenden die CPU.

GPU-Erkennung im laufenden Container prüfen:

```sh
docker compose exec voiceswap python -c "from app.devices import device_info; print(device_info())"
```

Ein erfolgreicher Geräteaufruf ersetzt keinen kompletten Trainingslauf.

## Stoppen und erneut starten

```sh
docker compose stop
docker compose up -d
```

Bei aktualisiertem Projekt wieder `docker compose up --build -d` verwenden.
Das Datenvolume bleibt beim Stoppen erhalten. **`down -v` löscht es.**

## Häufige Probleme

- **Docker nicht erreichbar:** Docker Desktop bzw. den Docker-Dienst starten.
- **GPU fehlt:** Windows: WSL2, Linux-Container und NVIDIA-Treiber prüfen.
  Linux: Container Toolkit und Docker-Konfiguration prüfen.
- **Speichermangel:** Trainings-Batch reduzieren, zunächst 1 oder 2; andere GPU-Anwendungen schließen.
- **Port belegt:** `VOICESWAP_PORT=7861` in `.env` eintragen und erneut mit `up -d` starten.

Protokoll: `docker compose logs --tail 100 voiceswap`.
Weiter: [Bedienung](usage.md) · [Sicherung und Wartung](maintenance.md).
