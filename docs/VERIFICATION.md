# Verifizierter Stand vom 25. Oktober 2026

## Korrektur: DirectML-Tongenerator (25. Oktober)

Ein numerischer Fehler wurde auf der RTX 5070 Ti mit DirectML 0.2.5/PyTorch 2.4.1
reproduziert: Die Multiplikation von Float-Pitchwerten mit ganzzahligen, gebroadcasteten
Samplepositionen erzeugte innerhalb eines Pitchframes konstante statt ansteigende
Phasenwerte. Der vorherige reine Ablauf-/Endlichkeitstest erkannte diese Klangursache
nicht. Samplepositionen und Harmonische haben jetzt ausdrücklich denselben
Gleitkommatyp wie die Tonhöhe; die GPU-Netze bleiben aktiv.

- Grundwellen mit variabler Tonhöhe bei 32/40/48 kHz über 1 und 32 Sekunden gegen
  eine unabhängige Phasenreferenz geprüft, einschließlich CUDA und DirectML.
- Harmonische mit festen Startphasen gegen CPU geprüft.
- 19 Tests in der DirectML-Umgebung erfolgreich, 7 CUDA-Fälle dort übersprungen;
  14 Grundwellen-/Harmonischentests in der CUDA-Umgebung erfolgreich, 7 DirectML-Fälle
  dort übersprungen. DirectML-Starttest einschließlich Training/Checkpoint erfolgreich.
- RMVPE bei einem synthetischen 220-Hz-Ton: maximale CPU/DirectML-Abweichung 0,083 Hz.
- HuBERT: relative RMS-Abweichung zur CPU rund 0,00044 % beim synthetischen Vergleich.
- Vollständiger Synthesizer mit identischen Testgewichten und festgesetztem Rauschen:
  relative RMS-Abweichung zur CPU unter 0,008 % für 1 und 3 Sekunden.

Dies belegt die numerische Korrektur auf der vorhandenen Hardware. Die RX 6750 XT,
die Aufnahme und das Modell des betroffenen Nutzers standen für diesen Vergleich
nicht zur Verfügung; die konkrete Hörqualität muss dort erneut geprüft werden.

## Ergänzung: Windows DirectML

Die native Windows-Ausgabe wurde mit `torch-directml 0.2.5.dev240914`, PyTorch
2.4.1 und einer RTX 5070 Ti **über DirectML** geprüft. CUDA wurde für diese Läufe
nicht verwendet. Eine AMD RX 6750 XT steht hier nicht zur Verfügung; deren
hardwareabhängiges Treiberverhalten ist deshalb noch nicht verifiziert. Die
Implementierung verwendet den herstellerübergreifenden DirectX-12-/DirectML-Weg.

Erfolgreich geprüft:

- Installation der separaten Umgebung, FFmpeg über WinGet, Frontend-Build und
  Start über `start-windows.cmd`; Adapterliste und `--check` funktionieren.
- 19 Backend-Tests in der DirectML-Umgebung. Darunter echte GPU-Gradiententests
  für Spektralverlust und relative Attention im Vergleich zur CPU sowie die
  Zurückweisung von Legacy-Pickle/TAR und TorchScript bei Modellimporten.
- Zwei Browser-Tests gegen die native App, einschließlich Batch-1-Voreinstellung,
  Upload, Navigation, mobiler Darstellung und Decodieren eines erzeugten Audios.
- Vollständiges RVC-v2-Training mit 1- und 5-Sekunden-Testaufnahmen, GPU-Generator
  und GPU-Discriminator, Modell-/Indexexport und erneuter Import.
- Fortsetzung aus den gespeicherten Generator-/Discriminator- und
  Optimizer-Zuständen bis Epoche 3; Indexerstellung in einem separaten Prozess
  vermeidet den Windows-Konflikt zwischen den OpenMP-Bibliotheken von FAISS und PyTorch.
- GPU-Stimmenaustausch mit RMVPE, FCPE und Parselmouth: WAV, 40 Sekunden FLAC
  bei 48 kHz über mehrere Abschnitte sowie MP3 bei 44,1 kHz.
- Die Konvertierungsprotokolle bestätigen `Synthesizer=privateuseone:0` und
  `HuBERT=privateuseone:0`; die App prüft die tatsächlichen Modellgeräte vor der Verarbeitung.
- Song-Verarbeitung mit Demucs auf CPU und Stimmenaustausch auf DirectML,
  einschließlich endlicher Signale und korrekter Dauer aller drei Ausgaben.
- Abbruch eines laufenden Auftrags.
- Nach den Änderungen erneut erfolgreiche CUDA-Konvertierung mit
  `Synthesizer=cuda:0`, `HuBERT=cuda:0` und gültiger Audioausgabe; Docker-Image baut.

DirectML ist ein gemischter Rechenweg: Spektralanalyse, RMVPE-GRU, Umordnung der
relativen Positionen, Gesangstrennung und einzelne nicht unterstützte Operatoren
verwenden die CPU. Training und Stimmenersetzung selbst verwenden die GPU-Netze.
Dies ist keine Aussage über die Leistung oder Kompatibilität jeder AMD-GPU und
jeder Treiberversion. Der Starttest auf dem Zielrechner ist deshalb obligatorisch.
Alle Integrationstests nutzten synthetisches Audio, keine Qualitätsbewertung echter Stimmen.

## Ursprünglicher NVIDIA-Docker-Test

Die Anwendung wurde unter Windows mit Docker Desktop (Linux-Container) auf einer
NVIDIA GeForce RTX 5070 Ti mit 16 GB VRAM geprüft. Der laufende Container verwendet
PyTorch 2.7.1 mit CUDA 12.8 und erkennt die Blackwell-GPU mit Compute Capability 12.0.

## Erfolgreiche Prüfungen

- 14 Backend-Tests: Uploads, Bibliothek, Bereichsabrufe für Audioplayer,
  Pfadvalidierung, Projekte, Auftragsparameter, sichere Modellimporte,
  Download-Prüfsummen, PCM-Normalisierung, Indexabfrage und Audio-Übergänge.
- TypeScript-/Vite-Produktionsbuild und Python-Lint-Prüfung.
- Zwei Browser-Tests gegen die Docker-App: Navigation, Formularzustand,
  Audio-Upload, Projektanlage, echte Audiowiedergabe-Metadaten und mobile Darstellung.
- GPU-Training mit lokal erzeugten synthetischen Audiodateien von 1 und 5 Sekunden,
  anschließend Export und erneuter Import von `.pth` und `.index`.
- Fortsetzung desselben Trainings aus gespeicherten Checkpoints von Epoche 1 auf 2.
- Abbruch eines tatsächlich laufenden Auftrags.
- GPU-Konvertierung mit RMVPE einschließlich Gesangstrennung durch Demucs und
  Downloads für Mix, neue Stimme und Begleitung.
- 40 Sekunden Audio mit FCPE und FLAC-Ausgabe bei 48 kHz: mehrere
  Verarbeitungsabschnitte mit unveränderter Gesamtdauer.
- Konvertierung mit Parselmouth, geänderter Tonhöhe und MP3-Ausgabe bei 44,1 kHz.
- CPU-Inferenz mit einem importierten Modell: 1 Sekunde Audio bei 40 kHz.
- Endliche, nicht leere Audiosignale und erwartete Dauer der Testausgaben.
- Alle vier Compose-Konfigurationen syntaktisch validiert.

Die ausführbaren Integrationstests stehen in `scripts/smoke.py` und
`scripts/check_extended.py`. Testmodelle und Testaufnahmen sind in der Bibliothek
als solche benannt. Sie sind keine für den produktiven Einsatz trainierten Stimmen.

## Grenzen dieser Prüfung

AMD ROCm und Intel XPU wurden mangels entsprechender Hardware nicht ausgeführt;
insbesondere das Intel-Containerimage ist experimentell. Ein vollständiges
CPU-Training wurde nicht durchgeführt. Die kurzen synthetischen Trainingsdaten
prüfen den technischen Ablauf, nicht die erreichbare Stimmqualität. Diese muss
mit geeigneten eigenen Sprach- oder Gesangsaufnahmen bewertet werden. Sehr große
Datensätze und mehrstündige Audiodateien wurden nicht im Lasttest geprüft.
