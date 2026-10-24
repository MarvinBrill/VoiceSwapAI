# NVIDIA / CUDA with Docker

[Guide index](README.md) · [Deutsch](../de/cuda.md)

## Requirements

- Windows x64 with Docker Desktop using WSL2/Linux containers, or Linux x86-64 with Docker Engine.
- An NVIDIA GPU with a suitable current driver. PyTorch 2.7.1 with CUDA 12.8 covers
  RTX 50 / Blackwell; the RTX 5070 Ti was tested directly.
- Docker Compose 2.30 or newer for `gpus: all`.
- The complete project, internet for the first build and sufficient disk space.

A separately installed CUDA Toolkit on the host is not required.

### Prepare Windows

Install the NVIDIA driver and Docker Desktop. Enable the WSL2 backend and use Linux
containers. Docker must be running. If WSL is outdated, run in PowerShell:

```powershell
wsl --update
```

Restart Docker Desktop if necessary. See [Docker GPU support on Windows](https://docs.docker.com/desktop/features/gpu/).

### Prepare Linux

Install the NVIDIA driver, Docker Engine with the Compose plugin, and the
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
using the instructions for your distribution. Configure the toolkit for Docker.
`nvidia-smi` must recognize the GPU on the host. A working host driver alone does
not give Docker access to the GPU.

## Start

From the project folder, in PowerShell or a Linux terminal:

```sh
docker compose up --build -d
docker compose ps
```

Open http://localhost:7860. Missing base weights are downloaded automatically.
In **System & Speicher** (system and storage), check that the expected NVIDIA GPU
and **CUDA** are displayed. Training and voice conversion use the GPU; audio I/O
and some supporting operations use the CPU.

Check device detection in the running container:

```sh
docker compose exec voiceswap python -c "from app.devices import device_info; print(device_info())"
```

Device detection alone does not verify a complete training run.

## Stop and restart

```sh
docker compose stop
docker compose up -d
```

After updating the project, use `docker compose up --build -d` again.
Stopping preserves the data volume. **`down -v` deletes it.**

## Common problems

- **Docker unavailable:** Start Docker Desktop or the Docker service.
- **GPU unavailable:** On Windows, check WSL2, Linux containers and the NVIDIA driver.
  On Linux, check the Container Toolkit and Docker configuration.
- **Out of memory:** Reduce the training batch to 1 or 2 and close other GPU applications.
- **Port occupied:** Add `VOICESWAP_PORT=7861` to `.env` and run `up -d` again.

Logs: `docker compose logs --tail 100 voiceswap`.
Next: [Using the app](usage.md) · [Backups and maintenance](maintenance.md).
