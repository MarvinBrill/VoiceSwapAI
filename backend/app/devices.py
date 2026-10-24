import os


def select_device():
    import torch

    requested = os.getenv("VOICESWAP_DEVICE", "auto")
    if requested == "cpu":
        return "cpu"
    if requested == "directml":
        try:
            import torch_directml

            index = int(os.getenv("VOICESWAP_DIRECTML_DEVICE", str(torch_directml.default_device())))
            if not 0 <= index < torch_directml.device_count():
                raise ValueError("GPU-Nummer liegt außerhalb der verfügbaren Geräte.")
            return str(torch_directml.device(index))
        except (ImportError, RuntimeError, ValueError) as error:
            raise RuntimeError(f"DirectML ist nicht verfügbar: {error}") from error
    if requested in ("auto", "cuda") and torch.cuda.is_available():
        return "cuda:0"
    if requested in ("auto", "xpu") and hasattr(torch, "xpu") and torch.xpu.is_available():
        return "xpu:0"
    if requested not in ("auto", "cpu"):
        raise RuntimeError(
            f"Das angeforderte Gerät {requested} ist nicht verfügbar. Treiber und Docker-GPU-Freigabe prüfen."
        )
    return "cpu"


def device_info():
    import torch

    try:
        device = select_device()
    except RuntimeError as error:
        return {
            "device": "unavailable",
            "name": "GPU nicht verfügbar",
            "error": str(error),
            "torch": torch.__version__,
        }
    if device.startswith("cuda"):
        properties = torch.cuda.get_device_properties(0)
        return {
            "device": device,
            "name": properties.name,
            "memory_gb": round(properties.total_memory / 1024**3, 1),
            "backend": "ROCm" if torch.version.hip else "CUDA",
            "torch": torch.__version__,
        }
    if device.startswith("xpu"):
        return {
            "device": device,
            "name": torch.xpu.get_device_name(0),
            "backend": "Intel XPU",
            "torch": torch.__version__,
        }
    if device.startswith("privateuseone"):
        import torch_directml

        index = int(device.split(":")[-1])
        return {
            "device": device,
            "name": torch_directml.device_name(index).rstrip("\x00"),
            "backend": "DirectML",
            "torch": torch.__version__,
            "note": "Training und Stimmenaustausch auf der GPU. Spektralanalyse und Gesangstrennung nutzen die CPU.",
        }
    return {"device": "cpu", "name": "CPU", "backend": "CPU", "torch": torch.__version__}
