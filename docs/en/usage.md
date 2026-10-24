# Using VoiceSwapAI

[Guide index](README.md) · [Deutsch](../de/usage.md)

Complete the appropriate setup first. Open http://localhost:7860 (or your chosen port).
In **System & Speicher** (system and storage), check the device and base weights.
An active download appears under **Ergebnisse** (results). Use **Fehlende Dateien
einrichten** (install missing files) if base files still need to be downloaded.

## Train a voice model

1. Open **Training** and name the project.
2. Add local audio recordings. Multiple files are supported; use the file overview
   to search, preview or remove recordings from the training dataset.
3. Use clean recordings of one voice. Music, reverb, noise and overlapping speakers
   reduce the quality of the training material.
4. Choose sample rate, epochs and batch size. Start with **40 kHz and batch 1**,
   especially with DirectML or unknown memory requirements. More epochs cannot
   replace good recordings. Leave **GPU-Cache** disabled initially.
5. Save the project and select **Training starten** (start training). The app prepares
   audio, extracts features, trains RVC v2 and builds the voice index.
6. Follow progress and logs under **Ergebnisse**. The completed model appears in
   **Modellbibliothek** (model library), where both `.pth` and `.index` can be downloaded.

Only locally added recordings are used as training data. Pretrained base weights
provide the starting point. Clips of 1–120 seconds and longer files are supported.
There is no fixed file-count or duration cap; disk space, RAM/VRAM and processing time
limit practical dataset size. The app splits training audio into segments.

## Resume training

Under **Ergebnisse → Training fortsetzen** (resume training), select a higher **total
epoch count**: increasing 100 to 150 means 50 additional epochs. Resuming requires
complete saved generator/discriminator checkpoints and the original training data.
An exported `.pth` alone is not sufficient.

## Replace a voice in audio

1. Import an exported RVC v1/v2 `.pth` in **Modellbibliothek**. Optionally add its
   matching `.index`. Imported models stay in the library for reuse.
2. Open **Voice Studio**, upload local audio or select files already in the library.
3. Choose the target model. Select **Stimme pur** for speech/isolated vocals, or
   **Kompletter Song** for separation of vocals/accompaniment followed by a new mix.
4. Adjust pitch, index strength, consonant protection, loudness envelope and pitch
   method. Start with the defaults. ±12 semitones shifts the voice by one octave.
   Under **Erweiterte Einstellungen → Stimmenlautstärke** (advanced settings → voice
   volume), adjust the new voice from **−24 to +12 dB** in 0.5 dB steps; **0 dB** is
   unchanged. This works in both voice-only and full-song mode. In song mode, voice
   gain is applied before mixing; accompaniment has its own control. If needed to
   prevent clipping, the final mix is turned down as a whole. Separate song stems
   are exported without these volume adjustments.
5. Choose WAV/FLAC at 24 bit or MP3 at 320 kbit/s.
6. Select **Stimme verwandeln** (convert voice). Listen to the result in the browser
   and download it. Song mode also provides separate new-vocal and accompaniment files.

CUDA/DirectML training and voice conversion use GPU networks. DirectML uses the CPU
for supporting operations and optional Demucs vocal separation. Long conversions
are processed in chunks with crossfaded transitions.

## Models and jobs

- Models must be exported RVC inference weights in PyTorch ZIP format.
  Arbitrary `.pth` networks, TorchScript, legacy pickle/TAR and raw `G_*.pth` checkpoints are unsuitable.
- Jobs run sequentially to avoid competing for GPU memory.
- **Abbrechen** (cancel) also stops child processes. Restarting marks interrupted
  jobs; it does not resume them automatically.
- A short synthetic smoke test does not establish voice quality. Use suitable
  recordings of your own speech or singing to train useful models.

[Backups and troubleshooting](maintenance.md).
