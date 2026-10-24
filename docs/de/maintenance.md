# Betrieb, Daten und Fehlerbehebung

[Übersicht](README.md) · [English](../en/maintenance.md)

## Datenstandorte

| Startweg | Standard-Speicher |
| --- | --- |
| Docker: CUDA, ROCm, XPU oder CPU | Volume `voiceswapai_voiceswap-data`, im Container `/data` |
| Natives Windows / DirectML | `data/` im Projektordner; optional durch `VOICESWAP_DATA` geändert |

Enthalten sind `library.sqlite3`, `uploads/`, `models/`, `assets/`, `training/`, `jobs/`
und `outputs/`. Die beiden Startwege teilen ihre Daten **nicht automatisch**.
Eine aus einem anderen Startweg heruntergeladene `.pth` und `.index` kann über die
Modellbibliothek importiert werden; dadurch werden keine Trainings-Checkpoints übertragen.

## Stoppen und aktualisieren

Aktive Aufträge zuerst abschließen oder gezielt abbrechen.

- **Docker:** Den Stoppbefehl aus der jeweiligen Hardware-Anleitung verwenden. Nach
  Aktualisierung der Projektdateien mit denselben Compose-Dateien `up --build -d` ausführen.
- **DirectML:** Im Startterminal Strg+C drücken. Projektdateien aktualisieren und
  `start-windows.cmd` erneut starten. `data/` beim Ersetzen der Projektdateien erhalten.

Die App nicht parallel aus zwei Prozessen mit demselben Datenspeicher betreiben.
Docker-`stop` und `down` erhalten das Volume. **`docker compose down -v` löscht die Daten.**

## Sichern

Für ein konsistentes Backup die App vorher stoppen. Den **gesamten Datenspeicher**
sichern; nur SQLite oder nur `.pth` reicht für vollständige Projekte nicht aus.

**DirectML:** Den kompletten Ordner `data/` an einen separaten Sicherungsort kopieren.
Zum Wiederherstellen bei gestoppter App die vollständige gesicherte Struktur als
Datenordner verwenden. Aktuelle Daten vor dem Ersetzen separat sichern.

**Docker:** Das Volume exportieren, z. B. mit einem kurzlebigen Hilfscontainer.
Mit `docker volume inspect voiceswapai_voiceswap-data` zuerst prüfen, dass das
gewünschte Volume existiert. Bei einem abweichenden Compose-Projektnamen den tatsächlichen
Volume-Namen verwenden. Bei einem Fehler nicht mit dem Backup fortfahren.
Vorher einen vorhandenen absoluten Backup-Ordner einsetzen. Der Befehl funktioniert
in PowerShell und einer Linux-Shell, wenn der Platzhalter ersetzt ist:

```sh
docker run --rm --mount type=volume,src=voiceswapai_voiceswap-data,dst=/source,readonly --mount "type=bind,src=ABSOLUTER_BACKUP_ORDNER,dst=/backup" alpine:3.21 tar -czf /backup/voiceswapai-backup.tar.gz -C /source .
```

Einen neuen Dateinamen verwenden, wenn dort bereits eine Sicherung liegt. Das Alpine-Image
wird ggf. heruntergeladen. Vor einer Wiederherstellung das bestehende Volume zusätzlich
sichern; das Archiv muss mit seiner ursprünglichen Ordnerstruktur in den Datenspeicher
zurückgespielt werden. Keine Wiederherstellung bei laufender App durchführen.

## Backend oder Port wechseln

Docker-Instanz zuerst stoppen, dann den vollständigen Startbefehl der neuen Hardware-
Anleitung verwenden. Die Compose-Varianten verwenden denselben Dienst und dasselbe
Volume; sie sind keine gleichzeitig zu startenden Dienste. Bei einem Wechsel immer bauen.

Für Docker `VOICESWAP_PORT=7861` in `.env` eintragen und erneut `up -d` mit den passenden
Compose-Dateien ausführen. DirectML verwendet stattdessen `--port 7861`.
Die Browseradresse ist dann http://localhost:7861.

## Fehler gezielt prüfen

| Problem | Prüfung |
| --- | --- |
| Seite öffnet nicht | Prozess/Container läuft? Richtiger Port? Bei Docker `ps` und `logs --tail 100 voiceswap` mit denselben `-f`-Dateien verwenden. |
| Basisdateien fehlen | Unter **System & Speicher** prüfen; Downloadprotokoll unter **Ergebnisse** ansehen; Internet und freien Platz prüfen. |
| GPU nicht verfügbar | Die Hardware-Anleitung verwenden; DirectML zusätzlich mit `--list-devices` und `--check` prüfen. |
| Training/Konvertierung fehlgeschlagen | Auftrag unter **Ergebnisse** öffnen und Protokoll lesen; Batch reduzieren bzw. Modellformat und Audio prüfen. |
| Import abgewiesen | Exportiertes RVC-Modell verwenden, kein Trainings-Checkpoint/TTS-Netz/TorchScript. |
| Nach Neustart fehlt die Bibliothek | Gleicher Datenordner bzw. Docker-Volume? Ein Wechsel zwischen Docker und nativem Start verwendet getrennte Speicher. |

Die Oberfläche ist standardmäßig nur lokal erreichbar und hat keine Benutzeranmeldung.
Öffentliche Bereitstellung ist nicht Bestandteil dieses Setups.
