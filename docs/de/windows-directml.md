# AMD unter Windows / DirectML

[Übersicht](README.md) · [English](../en/windows-directml.md)

Dieser Weg startet VoiceSwapAI **nativ unter Windows, ohne Docker**. Training und
Stimmenersetzung verwenden DirectML auf der GPU. Er ist auch für Intel- und NVIDIA-GPUs
mit geeignetem DirectX-12-Treiber gedacht. Für NVIDIA ist CUDA mit Docker der bereits geprüfte Standardweg.

## Voraussetzungen und Grenzen

- Windows 10/11 **x64**, aktueller Grafiktreiber und DirectX-12-fähige GPU.
- WinGet aus dem Windows App-Installer; `winget --version` muss funktionieren.
- Vollständiger entpackter Projektordner und Internet für die Erstinstallation.
- Genügend Platz für die eigene Python-Umgebung, Modelle und Trainingsdaten.

Die RX 6750 XT ist Ziel dieses Startwegs, wurde hier aber nicht direkt getestet.
Die vollständigen DirectML-Abläufe wurden auf einer RTX 5070 Ti geprüft. Daraus folgt
keine Garantie für jede AMD-Karte oder jeden Treiber. Der automatische GPU-Test muss
auf dem Zielrechner erfolgreich sein. [Microsoft: DirectML unter Windows](https://learn.microsoft.com/en-us/windows/ai/directml/pytorch-windows).

## Einrichten und starten

`start-windows.cmd` doppelklicken oder im Projektordner in PowerShell ausführen:

```powershell
.\start-windows.cmd
```

Beim ersten Start installiert der Launcher bei Bedarf **uv, Node.js LTS und FFmpeg über
WinGet**. uv richtet Python 3.12 ein. Die getrennte Umgebung `.venv-directml` erhält
die benötigten Python-Pakete; anschließend wird die Weboberfläche gebaut.
Falls Windows einen Installationsdialog anzeigt, diesen bestätigen. Es werden keine
Sicherheitsrichtlinien oder Antivirus-Ausnahmen geändert.

Danach prüft der Launcher echte GPU-Rechenoperationen, Trainingsgradienten und Checkpoints
und öffnet http://localhost:7860. Das Terminal während der Nutzung offen lassen.
**Strg+C beendet die App.** Beim nächsten Mal dieselbe Startdatei verwenden.

## Richtige GPU auswählen

```powershell
.\start-windows.cmd --list-devices
.\start-windows.cmd --device 0 --check
.\start-windows.cmd --device 0
```

`0` durch die Nummer der gewünschten Radeon aus der Liste ersetzen. Ohne `--device`
wird der DirectML-Standardadapter verwendet. Die Nummer bei späteren Starts erneut
angeben. Auch die Listen-/Prüfoptionen erledigen zunächst eine ggf. nötige Einrichtung.
Unter **System & Speicher** die GPU und **DirectML** kontrollieren.

Weitere Optionen:

```powershell
.\start-windows.cmd --port 7861
.\start-windows.cmd --no-browser
```

Bei Port 7861 die Adresse http://localhost:7861 verwenden.

## Was auf GPU und CPU läuft

- GPU: RVC-Trainingsnetze, Stimmen-Synthesizer, HuBERT und große Teile der Pitch-Netze.
- CPU: Spektralanalyse, RMVPE-GRU, bestimmte Umordnungen und nicht unterstützte Operatoren.
- **Kompletter Song:** Demucs trennt Gesang/Begleitung auf der CPU; anschließend wird
  die Stimme auf der GPU ersetzt. Dieser Ablauf kann länger dauern.

Die Oberfläche wählt bei DirectML zunächst Batch 1. Für die RX 6750 XT mit Batch 1
und 40 kHz beginnen. Erst nach einem erfolgreichen Lauf größere Batches ausprobieren.
Die Anzeige `PyTorch 2.4.1+cpu` ist normal: GPU-Beschleunigung liefert das separate
DirectML-Plugin. Den Backend-Namen und GPU-Namen prüfen, nicht nur diese Versionsendung.

## Daten und Probleme

Die App speichert standardmäßig alles in **`data/` im Projektordner**. Dieser Speicher
ist getrennt vom Docker-Volume. Für eine Sicherung zuerst stoppen und `data/` vollständig kopieren.

- **WinGet fehlt:** Windows App-Installer installieren/aktualisieren, neues Terminal öffnen.
- **GPU-Test schlägt fehl:** Treiber aktualisieren und Adapter mit `--list-devices` prüfen.
  Fehlertext für die Diagnose aufbewahren; das Programm weicht nicht still auf CPU aus.
- **Port belegt:** Andere Instanz stoppen oder `--port 7861` verwenden.
- **Zu wenig VRAM:** Batch 1, GPU-Cache im Training ausgeschaltet lassen und andere GPU-Programme schließen.
- **Update:** App stoppen, Projektdateien aktualisieren und Startdatei erneut ausführen.
  Abhängigkeiten und Frontend werden bei Änderungen automatisch erneuert.

Weiter: [Bedienung](usage.md) · [Wartung](maintenance.md).
