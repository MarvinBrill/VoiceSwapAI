# AMD unter Linux / ROCm mit Docker

[Übersicht](README.md) · [English](../en/amd-rocm.md)

**Status: vorbereitet, nicht auf AMD-Hardware getestet.** Diese Konfiguration ist für
einen nativen Linux-Host, nicht für AMD unter Windows mit Docker Desktop.
Für Windows die [DirectML-Anleitung](windows-directml.md) verwenden.

## Voraussetzungen

- Linux x86-64 mit Docker Engine und Compose mindestens 2.30.
- Eine zum eingesetzten **ROCm 6.3** passende GPU, Distribution und AMD-Host-Treiber.
- Die Gerätedateien `/dev/kfd` und `/dev/dri` müssen vorhanden sein.
- Vollständiger Projektordner und Internet beim ersten Build.

Die RX 6750 XT (`gfx1031`) ist kein offiziell unterstütztes Ziel dieses ROCm-Stacks.
Es wird kein Architektur-Override automatisch gesetzt. Ein neuerer Treiber oder eine
neuere AMD-Karte macht die festgelegte ROCm-Version nicht automatisch kompatibel.
Vorher die [ROCm-6.3-Kompatibilität](https://rocm.docs.amd.com/en/docs-6.3.0/compatibility/compatibility-matrix.html) prüfen.

## Geräteberechtigungen einrichten

Im Linux-Terminal:

```sh
ls -l /dev/kfd /dev/dri/render*
getent group video render
```

Im Projektordner eine `.env` anlegen oder bestehende Einträge ergänzen. Die Werte
aus der Ausgabe bzw. den tatsächlichen Gerätegruppen übernehmen. Beispielwerte:

```dotenv
VIDEO_GID=44
RENDER_GID=109
```

Die Zahlen sind nicht auf allen Distributionen gleich. Fehlende Gerätedateien müssen
durch eine passende Host-Treiberinstallation behoben werden; Docker erzeugt sie nicht.

## Starten

```sh
docker compose -f compose.yaml -f compose.amd.yaml up --build -d
docker compose -f compose.yaml -f compose.amd.yaml ps
```

http://localhost:7860 öffnen und die Basisgewichte herunterladen lassen.
Unter **System & Speicher** müssen die AMD-GPU und **ROCm** erscheinen.
Die Konfiguration setzt intern `VOICESWAP_DEVICE=cuda`: PyTorch verwendet diesen
Gerätenamen auch für ROCm. Das bedeutet hier nicht, dass NVIDIA benötigt wird.

```sh
docker compose -f compose.yaml -f compose.amd.yaml exec voiceswap python -c "from app.devices import device_info; print(device_info())"
```

Geräteerkennung allein bestätigt noch keinen kompletten Trainings-/Konvertierungslauf.
Mit eigenen kurzen Audios, Batch 1 und 40 kHz beginnen; Ergebnisse prüfen, bevor ein
langer Trainingslauf gestartet wird.

## Stoppen, Updates und Diagnose

```sh
docker compose -f compose.yaml -f compose.amd.yaml stop
docker compose -f compose.yaml -f compose.amd.yaml up --build -d
docker compose -f compose.yaml -f compose.amd.yaml logs --tail 100 voiceswap
```

Auch bei späteren Starts beide `-f`-Dateien verwenden. Ohne die AMD-Datei würde die
NVIDIA-Konfiguration geladen. Bei `Permission denied` Gerätegruppen prüfen; bei
fehlenden GPU-Kernels die Kompatibilität von GPU, Treiber und ROCm prüfen.
Kein `privileged` und keine pauschalen Geräteberechtigungen sind für dieses Setup vorgesehen.

Daten bleiben im Docker-Volume. [Bedienung](usage.md) · [Sicherung und Backendwechsel](maintenance.md).
