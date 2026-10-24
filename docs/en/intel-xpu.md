# Intel on Linux / XPU with Docker

[Guide index](README.md) · [Deutsch](../de/intel-xpu.md)

**Experimental and not tested on hardware.** This variant uses `Dockerfile.intel`,
Intel GPU libraries inside the container and PyTorch/torchaudio 2.7.1 with XPU.
On Windows, use the separate [DirectML launcher](windows-directml.md).

## Requirements

- Native Linux x86-64 with Docker Engine and Compose 2.30 or newer.
- An Intel GPU supported by the configured PyTorch XPU and Intel driver versions.
- A suitable host kernel/graphics driver and render devices under `/dev/dri`.
- Internet access, including Intel's package server during the build.

Installing drivers inside the image does not replace the host driver. The current
[PyTorch XPU documentation](https://docs.pytorch.org/docs/stable/notes/get_start_xpu.html)
describes the platform; support in newer versions does not automatically apply to
the pinned PyTorch 2.7.1 stack. This Intel image has not been built or run here.

## Check device groups

```sh
ls -l /dev/dri/render*
getent group video render
```

Create or edit `.env` in the project folder with the IDs of your device groups.
These numbers are examples only:

```dotenv
VIDEO_GID=44
RENDER_GID=109
```

## Start and verify

```sh
docker compose -f compose.yaml -f compose.intel.yaml up --build -d
docker compose -f compose.yaml -f compose.intel.yaml ps
docker compose -f compose.yaml -f compose.intel.yaml exec voiceswap python -c "from app.devices import device_info; print(device_info())"
```

Open http://localhost:7860. **System & Speicher** must show the Intel adapter and
**Intel XPU**. Once base weights are ready, try training and conversion with batch 1
and short local recordings. Do not assume reliable operation from device detection alone.

## Stop and troubleshoot

```sh
docker compose -f compose.yaml -f compose.intel.yaml stop
docker compose -f compose.yaml -f compose.intel.yaml logs --tail 100 voiceswap
```

Use the same start command with both `-f` files for updates and subsequent starts.
Check render groups for access errors. For build failures, check Intel's repository
and package availability; for XPU errors, check host drivers and GPU compatibility.
[CPU mode](cpu.md) is an alternative.

[Usage](usage.md) · [Backups and switching backends](maintenance.md).
