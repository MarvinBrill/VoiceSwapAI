# VoiceSwapAI bedienen

[Übersicht](README.md) · [English](../en/usage.md)

Zuerst den passenden Startweg einrichten. Im Browser http://localhost:7860 öffnen
(oder den selbst gewählten Port). Unter **System & Speicher** GPU/CPU und Basisgewichte
prüfen. Ein laufender Basisdownload erscheint unter **Ergebnisse**; fehlende Dateien
können über **Fehlende Dateien einrichten** nachgeladen werden.

## Ein Voice-Modell trainieren

1. **Training** öffnen und dem Projekt einen Namen geben.
2. Lokale Audioaufnahmen hinzufügen. Mehrere Dateien sind möglich; in der Übersicht
   lassen sie sich suchen, vorhören und aus dem Trainingsdatensatz entfernen.
3. Saubere Aufnahmen einer einzelnen Stimme verwenden. Musik, Hall, Rauschen und
   mehrere gleichzeitige Sprecher verschlechtern die Trainingsgrundlage.
4. Samplerate, Epochen und Batch-Größe einstellen. Mit **40 kHz und Batch 1** beginnen,
   insbesondere bei DirectML oder unbekanntem Speicherbedarf. Mehr Epochen ersetzen
   keine guten Aufnahmen. **GPU-Cache** zunächst ausgeschaltet lassen.
5. Projekt speichern und **Training starten**. Die App bereitet Audio auf, extrahiert
   Merkmale, trainiert RVC v2 und erzeugt den Stimmenindex.
6. Fortschritt und Protokoll unter **Ergebnisse** verfolgen. Das fertige Modell erscheint
   automatisch in der **Modellbibliothek**. Dort `.pth` und `.index` herunterladen.

Trainiert wird nur mit den lokal hinzugefügten Aufnahmen. Vortrainierte Basisgewichte
dienen als Ausgangspunkt. Clips von 1–120 Sekunden sind möglich, längere ebenso.
Es gibt keine feste Dateianzahl- oder Dauergrenze; Speicherplatz, RAM/VRAM und Laufzeit
begrenzen die praktische Größe. Die App teilt Aufnahmen für das Training in Abschnitte.

## Training fortsetzen

Unter **Ergebnisse → Training fortsetzen** eine höhere **Gesamtepochenzahl** wählen:
Nach 100 Epochen bedeutet 150 beispielsweise 50 zusätzliche Epochen. Fortsetzen braucht
vollständige gespeicherte Generator-/Discriminator-Checkpoints und die ursprünglichen
Trainingsdaten. Ein exportiertes `.pth` allein reicht dafür nicht.

## Stimmen in Audio ersetzen

1. Unter **Modellbibliothek** ein exportiertes RVC-v1/v2-`.pth` importieren. Optional
   den passenden `.index` hinzufügen. Ein importiertes Modell bleibt wiederverwendbar gespeichert.
2. **Voice Studio** öffnen, lokale Audios hinzufügen oder bereits vorhandene auswählen.
3. Das Zielmodell wählen. **Stimme pur** für Sprache/isolierten Gesang wählen;
   **Kompletter Song** trennt zuerst Gesang und Begleitung und mischt sie anschließend neu.
4. Tonhöhe, Indexstärke, Konsonantenschutz, Lautstärkeverlauf und Pitch-Verfahren anpassen.
   Zum Einstieg die Standardwerte verwenden. ±12 Halbtöne ändern die Stimme um eine Oktave.
   Unter **Erweiterte Einstellungen → Stimmenlautstärke** lässt sich die neue Stimme
   von **−24 bis +12 dB** in 0,5-dB-Schritten anpassen; **0 dB** verändert nichts.
   Der Regler wirkt bei **Stimme pur** und **Kompletter Song**. Im Song-Modus wird die
   Stimme vor dem Mischen verstärkt; die Begleitung hat ihren eigenen Regler.
   Bei drohender Übersteuerung wird der fertige Mix insgesamt abgesenkt. Die separaten
   Song-Spuren werden ohne diese Lautstärkeanpassungen exportiert.
5. Exportformat wählen: WAV/FLAC mit 24 Bit oder MP3 mit 320 kbit/s.
6. **Stimme verwandeln** starten. Das fertige Audio im Browser anhören und herunterladen.
   Beim Song-Modus gibt es außerdem neue Stimme und Begleitung als separate Downloads.

Training und Stimmenersetzung nutzen bei CUDA/DirectML die GPU-Netze. Im DirectML-Modus
laufen Hilfsoperationen und die optionale Demucs-Gesangstrennung auf der CPU.
Lange Konvertierungen werden abschnittsweise verarbeitet; die Abschnitte werden überblendet.

## Modelle und Aufträge

- Akzeptiert werden exportierte RVC-Inferenzmodelle im PyTorch-ZIP-Format.
  Beliebige `.pth`-Netze, TorchScript, Legacy-Pickle/TAR und rohe `G_*.pth`-Checkpoints sind ungeeignet.
- Aufträge laufen nacheinander, damit sie nicht gleichzeitig um den GPU-Speicher konkurrieren.
- **Abbrechen** beendet auch zugehörige Unterprozesse. Ein Neustart markiert unterbrochene Aufträge;
  er setzt sie nicht automatisch fort.
- Ein kurzer synthetischer Funktionstest belegt keine gute Stimmqualität. Für nutzbare
  Modelle eigene geeignete Sprach-/Gesangsaufnahmen verwenden.

[Daten sichern und Probleme lösen](maintenance.md).
