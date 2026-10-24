# Operation, storage and troubleshooting

[Guide index](README.md) · [Deutsch](../de/maintenance.md)

## Data locations

| Startup method | Default storage |
| --- | --- |
| Docker: CUDA, ROCm, XPU or CPU | Volume `voiceswapai_voiceswap-data`, mounted at `/data` |
| Native Windows / DirectML | `data/` in the project folder; optionally overridden with `VOICESWAP_DATA` |

Storage contains `library.sqlite3`, `uploads/`, `models/`, `assets/`, `training/`, `jobs/`
and `outputs/`. Native and Docker setups **do not automatically share data**.
You can import a `.pth` and `.index` downloaded from another setup into the model
library; this does not transfer the training checkpoints needed to resume training.

## Stop and update

Let active jobs finish or cancel them deliberately first.

- **Docker:** Use the stop command from the relevant hardware guide. After updating
  project files, run `up --build -d` with the same Compose files.
- **DirectML:** Press Ctrl+C in the launcher terminal. Update project files and run
  `start-windows.cmd` again. Preserve `data/` when replacing project files.

Do not run two app processes against the same data store at once.
Docker `stop` and `down` preserve the volume. **`docker compose down -v` deletes the data.**

## Back up

Stop the app before taking a consistent backup. Copy the **complete data store**;
SQLite alone or `.pth` files alone cannot restore full projects.

**DirectML:** Copy all of `data/` to a separate backup location. To restore, use the
complete saved directory structure as the data folder while the app is stopped.
Back up current data separately before replacing it.

**Docker:** Export the volume, for example with a temporary helper container.
First run `docker volume inspect voiceswapai_voiceswap-data` to confirm that the
intended volume exists. If using a different Compose project name, use its actual
volume name instead. Do not continue with the backup if this check fails.
Replace the placeholder with an existing absolute backup directory first. This command
works in PowerShell and a Linux shell once that placeholder is replaced:

```sh
docker run --rm --mount type=volume,src=voiceswapai_voiceswap-data,dst=/source,readonly --mount "type=bind,src=ABSOLUTE_BACKUP_DIRECTORY,dst=/backup" alpine:3.21 tar -czf /backup/voiceswapai-backup.tar.gz -C /source .
```

Choose a new archive filename if a previous backup already exists there. The Alpine
image is downloaded if necessary. Before restoring, also back up the existing volume;
restore the archive's original directory structure into the data store. Never restore
while the app is running.

## Switch backend or port

Stop the Docker instance first, then use the complete start command from the new
hardware guide. Compose variants use the same service and volume; they are not
separate services intended to run together. Always rebuild when switching backends.

For Docker, add `VOICESWAP_PORT=7861` to `.env` and run `up -d` with the appropriate
Compose files again. DirectML uses `--port 7861` instead.
The browser address then becomes http://localhost:7861.

## Diagnose problems

| Problem | What to check |
| --- | --- |
| Page does not open | Is the process/container running? Correct port? For Docker, use `ps` and `logs --tail 100 voiceswap` with the same `-f` files. |
| Missing base files | Check **System & Speicher**, download logs under **Ergebnisse**, internet access and free space. |
| GPU unavailable | Follow the hardware guide; for DirectML also use `--list-devices` and `--check`. |
| Training/conversion failed | Open the job log under **Ergebnisse**; reduce the batch size or check model format and source audio. |
| Model import rejected | Use exported RVC weights, not a training checkpoint, TTS network or TorchScript program. |
| Library missing after restart | Check the data directory/volume. Docker and native starts use separate storage. |

The interface is local-only by default and has no user authentication. Public hosting
is not part of this setup.
