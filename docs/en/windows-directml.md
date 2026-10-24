# AMD on Windows / DirectML

[Guide index](README.md) · [Deutsch](../de/windows-directml.md)

This path runs VoiceSwapAI **natively on Windows, without Docker**. Training and voice
conversion use the GPU through DirectML. It also targets Intel and NVIDIA GPUs with
suitable DirectX 12 drivers. For NVIDIA, CUDA with Docker remains the tested default path.

## Requirements and limitations

- Windows 10/11 **x64**, a current graphics driver and a DirectX-12-capable GPU.
- WinGet from Windows App Installer; `winget --version` must work.
- The complete extracted project and internet access for initial setup.
- Enough disk space for a separate Python environment, models and training data.

The RX 6750 XT is a target for this setup but has not been tested directly here.
Complete DirectML workflows were tested on an RTX 5070 Ti. This does not guarantee
compatibility with every AMD card or driver. The automatic GPU check must pass on
the target computer. [Microsoft: DirectML on Windows](https://learn.microsoft.com/en-us/windows/ai/directml/pytorch-windows).

## Install and start

Double-click `start-windows.cmd`, or run this in PowerShell from the project folder:

```powershell
.\start-windows.cmd
```

On first launch, the script installs **uv, Node.js LTS and FFmpeg through WinGet** if
needed. uv sets up Python 3.12. Python packages are installed in the separate
`.venv-directml` environment, and the web interface is built automatically.
Confirm Windows installation dialogs if shown. The launcher does not modify
security policies or add antivirus exclusions.

The launcher then checks actual GPU calculations, training gradients and checkpoints
and opens http://localhost:7860. Keep the terminal open while using the app.
**Press Ctrl+C to stop.** Use the same launcher for subsequent starts.

## Select the correct GPU

```powershell
.\start-windows.cmd --list-devices
.\start-windows.cmd --device 0 --check
.\start-windows.cmd --device 0
```

Replace `0` with the number of the Radeon adapter in the list. Without `--device`,
the DirectML default adapter is selected. Supply the number again on subsequent
starts. The list/check options also perform any required initial setup first.
In **System & Speicher**, verify the GPU name and **DirectML**.

Other options:

```powershell
.\start-windows.cmd --port 7861
.\start-windows.cmd --no-browser
```

When using port 7861, open http://localhost:7861.

## GPU and CPU work

- GPU: RVC training networks, the voice synthesizer, HuBERT and large parts of the pitch networks.
- CPU: spectral analysis, the RMVPE GRU, some tensor rearrangements and unsupported operators.
- **Kompletter Song** (complete song): Demucs separates vocals/accompaniment on the CPU;
  the voice is then replaced on the GPU. This workflow can take longer.

The interface initially selects batch size 1 for DirectML. Start with batch 1 and
40 kHz on an RX 6750 XT, increasing the batch only after a successful run.
Seeing `PyTorch 2.4.1+cpu` is normal: the separate DirectML plugin provides GPU
acceleration. Check the backend and adapter name rather than the version suffix.

## Storage and troubleshooting

By default, all app data is stored in **`data/` inside the project folder**. This is
separate from the Docker volume. Stop the app before copying all of `data/` for a backup.

- **WinGet missing:** Install/update Windows App Installer, then open a new terminal.
- **GPU check fails:** Update the graphics driver and check `--list-devices`.
  Keep the error text for diagnosis; the launcher does not silently switch to CPU.
- **Port occupied:** Stop the other instance or use `--port 7861`.
- **Insufficient VRAM:** Use batch 1, leave GPU dataset caching disabled and close other GPU programs.
- **Update:** Stop the app, update project files and run the launcher again.
  Changed dependency requirements and frontend files are processed automatically.

Next: [Using the app](usage.md) · [Maintenance](maintenance.md).
