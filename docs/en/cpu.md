# CPU mode with Docker

[Guide index](README.md) · [Deutsch](../de/cpu.md)

This mode requires no GPU passthrough. **Training and voice conversion run on the CPU**
and are considerably slower. CPU conversion has been tested; full CPU training has not.

## Requirements

- Windows x64 with Docker Desktop using Linux containers, or Linux x86-64 with Docker Engine.
- Docker Compose 2.30 or newer and the complete project folder.
- Internet for installation/base weights, enough RAM and free disk space.

This stack is not validated on Apple Silicon/ARM64; some pinned packages may be
unavailable. Mac GPU acceleration through Metal/MPS is not implemented.

## Start

From the project folder:

```sh
docker compose -f compose.yaml -f compose.cpu.yaml up --build -d
docker compose -f compose.yaml -f compose.cpu.yaml ps
```

Open http://localhost:7860. Missing base weights are downloaded automatically.
**System & Speicher** must show **CPU**. Start with batch 1 and short local recordings.
Vocal separation also uses CPU time in this mode.

## Stop and restart

```sh
docker compose -f compose.yaml -f compose.cpu.yaml stop
docker compose -f compose.yaml -f compose.cpu.yaml up -d
```

Add `--build` when starting after project changes. Always include both `-f` files;
otherwise Docker loads the default NVIDIA configuration.

Logs:

```sh
docker compose -f compose.yaml -f compose.cpu.yaml logs --tail 100 voiceswap
```

Stopping preserves the Docker volume. [Usage](usage.md) · [Maintenance](maintenance.md).
