# AMD on Linux / ROCm with Docker

[Guide index](README.md) · [Deutsch](../de/amd-rocm.md)

**Status: prepared, not tested on AMD hardware.** This configuration requires a native
Linux host. It is not the AMD setup for Windows Docker Desktop. On Windows, use
[DirectML](windows-directml.md).

## Requirements

- Linux x86-64 with Docker Engine and Compose 2.30 or newer.
- GPU, distribution and AMD host driver compatible with the configured **ROCm 6.3** stack.
- Both `/dev/kfd` and `/dev/dri` must exist on the host.
- The complete project and internet access for the first build.

The RX 6750 XT (`gfx1031`) is not an officially supported target of this ROCm stack.
No architecture override is set automatically. A newer driver or newer AMD card
does not automatically make the pinned ROCm version compatible.
Check the [ROCm 6.3 compatibility matrix](https://rocm.docs.amd.com/en/docs-6.3.0/compatibility/compatibility-matrix.html) first.

## Configure device permissions

In a Linux terminal:

```sh
ls -l /dev/kfd /dev/dri/render*
getent group video render
```

Create or edit `.env` in the project folder. Use the group IDs from your output and
actual device ownership. These are example values only:

```dotenv
VIDEO_GID=44
RENDER_GID=109
```

IDs differ between distributions. Missing device files must be fixed by installing
a suitable host driver; Docker cannot create the required GPU interfaces.

## Start

```sh
docker compose -f compose.yaml -f compose.amd.yaml up --build -d
docker compose -f compose.yaml -f compose.amd.yaml ps
```

Open http://localhost:7860 and allow base weights to download.
**System & Speicher** must show the AMD GPU and **ROCm**. Internally the configuration
sets `VOICESWAP_DEVICE=cuda`: PyTorch uses this device name for ROCm too. NVIDIA
hardware is not required for this configuration.

```sh
docker compose -f compose.yaml -f compose.amd.yaml exec voiceswap python -c "from app.devices import device_info; print(device_info())"
```

Device detection alone does not verify a full training/conversion workflow. Start
with short local recordings, batch 1 and 40 kHz, and check the result before a long run.

## Stop, update and diagnose

```sh
docker compose -f compose.yaml -f compose.amd.yaml stop
docker compose -f compose.yaml -f compose.amd.yaml up --build -d
docker compose -f compose.yaml -f compose.amd.yaml logs --tail 100 voiceswap
```

Always include both `-f` files, including on later starts. Omitting the AMD file
selects the NVIDIA configuration. For `Permission denied`, check device groups.
For missing GPU kernels, check GPU, driver and ROCm compatibility. This setup does
not require `privileged` mode or broadly relaxing device permissions.

Data remains in the Docker volume. [Usage](usage.md) · [Backups and switching backends](maintenance.md).
