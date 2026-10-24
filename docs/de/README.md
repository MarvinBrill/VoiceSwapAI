# VoiceSwapAI – Anleitungen

[English](../en/README.md) · [Projektübersicht](../../README.md)

## Den passenden Startweg wählen

| Rechner | Anleitung | Stand |
| --- | --- | --- |
| NVIDIA unter Windows oder Linux | [CUDA mit Docker](cuda.md) | Training und Stimmenersetzung auf RTX 5070 Ti geprüft |
| AMD unter Windows, z. B. RX 6750 XT | [DirectML ohne Docker](windows-directml.md) | DirectML auf RTX geprüft; RX 6750 XT selbst nicht getestet |
| Intel oder NVIDIA unter Windows mit DirectX 12 | [DirectML ohne Docker](windows-directml.md) | Herstellerübergreifender Weg; Treiber-/Kartenkompatibilität prüfen |
| Unterstützte AMD-GPU unter Linux | [ROCm mit Docker](amd-rocm.md) | Vorbereitet, nicht auf AMD-Hardware getestet |
| Unterstützte Intel-GPU unter Linux | [Intel XPU mit Docker](intel-xpu.md) | Experimentell, nicht hardwaregetestet |
| Ohne nutzbare GPU-Beschleunigung | [CPU mit Docker](cpu.md) | CPU-Konvertierung geprüft; vollständiges CPU-Training nicht geprüft |

DirectML und CUDA beschleunigen sowohl Training als auch Stimmenersetzung.
Im DirectML-Modus bleiben einige Hilfsoperationen und die Gesangstrennung auf der CPU.
Vulkan und Apple Metal/MPS sind nicht implementiert. Keine pauschale Zusage für jede GPU.

## Vor dem Start

1. Den vollständigen aktuellen Projektordner herunterladen oder klonen und ggf. entpacken.
   Nur eine Compose-Datei oder die Startdatei allein reicht nicht aus.
2. Ein Terminal im Projektordner öffnen. Dort müssen `compose.yaml`, `backend/`,
   `frontend/`, `engine/` und `start-windows.cmd` liegen.
3. Der passenden Hardware-Anleitung folgen. Alle dortigen Befehle beginnen im Projektordner.

Installation und erste Modelldownloads benötigen Internet. Die RVC-Basisgewichte
belegen ungefähr 1 GB; Demucs wird bei der ersten Song-Verarbeitung zusätzlich geladen.
Für Images, Laufzeit, Modelle und Checkpoints etwa 20 GB freien Platz als Ausgangspunkt
einplanen, für große Trainingsdaten mehr. Danach können vorbereitete Verfahren offline laufen.

## Weitere Anleitungen

- [Training, Stimmenersetzung, Anhören und Downloads](usage.md)
- [Stoppen, Updates, Daten, Sicherungen und Fehlerbehebung](maintenance.md)
- [Lokale Entwicklung und Tests](development.md)
- [Was tatsächlich getestet wurde](../VERIFICATION.md)

Die Weboberfläche ist derzeit deutschsprachig. Standardadresse: http://localhost:7860.
Die App verarbeitet Audio lokal und benötigt kein Benutzerkonto.
