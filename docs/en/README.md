# VoiceSwapAI guides

[Deutsch](../de/README.md) · [Project overview (German)](../../README.md)

## Choose your setup

| Computer | Guide | Verification status |
| --- | --- | --- |
| NVIDIA on Windows or Linux | [CUDA with Docker](cuda.md) | Training and voice conversion tested on RTX 5070 Ti |
| AMD on Windows, including RX 6750 XT | [DirectML without Docker](windows-directml.md) | DirectML tested on RTX; RX 6750 XT itself not tested |
| Intel or NVIDIA on Windows with DirectX 12 | [DirectML without Docker](windows-directml.md) | Cross-vendor path; verify adapter and driver compatibility |
| Supported AMD GPU on Linux | [ROCm with Docker](amd-rocm.md) | Prepared, not tested on AMD hardware |
| Supported Intel GPU on Linux | [Intel XPU with Docker](intel-xpu.md) | Experimental, not tested on hardware |
| No usable GPU acceleration | [CPU with Docker](cpu.md) | CPU conversion tested; full CPU training not tested |

DirectML and CUDA accelerate both training and voice conversion. DirectML still uses
the CPU for some supporting operations and vocal separation. Vulkan and Apple Metal/MPS
are not implemented. Compatibility with every GPU is not guaranteed.

## Before starting

1. Download or clone the complete current project and extract it if necessary.
   A Compose file or launcher on its own is not sufficient.
2. Open a terminal in the project folder containing `compose.yaml`, `backend/`,
   `frontend/`, `engine/` and `start-windows.cmd`.
3. Follow the guide for your hardware. All commands in those guides start in the project folder.

Installation and initial model downloads require internet access. RVC base weights
take approximately 1 GB; Demucs is downloaded separately for the first complete-song job.
Allow approximately 20 GB of free space initially for images, runtimes, models and
checkpoints, and more for large datasets. Prepared methods can then run offline.

## More guides

- [Training, voice conversion, playback and downloads](usage.md)
- [Stopping, updates, storage, backups and troubleshooting](maintenance.md)
- [Local development and testing](development.md)
- [Detailed verification record (German)](../VERIFICATION.md)

The web interface currently uses German labels; the English guides explain those labels.
Default address: http://localhost:7860. Audio processing is local and requires no account.
