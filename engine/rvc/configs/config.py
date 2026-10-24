"""VoiceSwapAI device adapter; replaces the upstream Gradio CLI configuration."""
import os
import torch


def get_device():
    requested = os.getenv("VOICESWAP_DEVICE", "auto")
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "directml":
        import torch_directml
        index = int(os.getenv("VOICESWAP_DIRECTML_DEVICE", str(torch_directml.default_device())))
        if not 0 <= index < torch_directml.device_count():
            raise RuntimeError("DirectML GPU index is unavailable")
        return torch_directml.device(index)
    if requested in ("cuda", "auto") and torch.cuda.is_available():
        return torch.device("cuda:0")
    if requested in ("xpu", "auto") and hasattr(torch, "xpu") and torch.xpu.is_available():
        return torch.device("xpu:0")
    if requested not in ("auto", "cpu"):
        raise RuntimeError(f"Requested device {requested} is unavailable")
    return torch.device("cpu")


def get_device_dtype_sm(idx):
    if get_device().type != "cuda":
        return torch.device("cpu"), torch.float32, 0, 0
    properties = torch.cuda.get_device_properties(idx)
    sm = 0 if torch.version.hip else properties.major + properties.minor / 10
    dtype = torch.float16 if torch.version.hip or sm >= 7 else torch.float32
    return torch.device(f"cuda:{idx}"), dtype, sm, properties.total_memory / 1024**3


def get_training_dtype():
    # FP32 is robust for adversarial RVC training across backends.
    return torch.float32


infer_device = get_device()
infer_dtype = get_device_dtype_sm(0)[1] if infer_device.type == "cuda" else torch.float32


class Config:
    def __init__(self):
        self.device = str(infer_device)
        self.dtype = infer_dtype
        self.is_half = infer_dtype == torch.float16
        self.x_pad, self.x_query, self.x_center, self.x_max = 1, 6, 30, 32
        self.cuda_graph = False
