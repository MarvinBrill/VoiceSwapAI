import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest
import torch

from app.checkpoints import load_voice_weights
from app.devices import select_device


def test_legacy_weights_are_rejected_before_deserialization(tmp_path, monkeypatch):
    path = tmp_path / "legacy.pth"
    torch.save({"weight": torch.zeros(1)}, path, _use_new_zipfile_serialization=False)

    def forbidden(*args, **kwargs):
        pytest.fail("Legacy file reached torch.load")

    monkeypatch.setattr(torch, "load", forbidden)
    with pytest.raises(ValueError, match="ZIP"):
        load_voice_weights(path)


def test_torchscript_is_not_accepted_as_voice_weights(tmp_path, monkeypatch):
    path = tmp_path / "program.pth"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("program/constants.pkl", b"test")
        archive.writestr("program/data.pkl", b"test")

    def forbidden(*args, **kwargs):
        pytest.fail("TorchScript file reached torch.load")

    monkeypatch.setattr(torch, "load", forbidden)
    with pytest.raises(ValueError, match="TorchScript"):
        load_voice_weights(path)


def test_directml_selects_explicit_adapter_and_rejects_missing_one(monkeypatch):
    fake = SimpleNamespace(
        default_device=lambda: 0, device_count=lambda: 2, device=lambda i: f"privateuseone:{i}"
    )
    monkeypatch.setitem(sys.modules, "torch_directml", fake)
    monkeypatch.setenv("VOICESWAP_DEVICE", "directml")
    monkeypatch.setenv("VOICESWAP_DIRECTML_DEVICE", "1")
    assert select_device() == "privateuseone:1"
    monkeypatch.setenv("VOICESWAP_DIRECTML_DEVICE", "2")
    with pytest.raises(RuntimeError, match="DirectML"):
        select_device()


@pytest.mark.skipif(
    importlib.util.find_spec("torch_directml") is None, reason="Separate DirectML runtime required"
)
def test_directml_spectral_loss_preserves_gpu_gradient():
    import torch_directml

    if torch_directml.device_count() == 0:
        pytest.skip("No DirectML adapter")
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine/rvc"))
    from train.mel_processing import mel_spectrogram_torch

    device = torch_directml.device()
    torch.manual_seed(18)
    cpu = torch.randn(1, 4096, requires_grad=True)
    gpu = cpu.detach().to(device).requires_grad_()
    arguments = (512, 40, 40000, 128, 512, 0, 20000)
    expected = mel_spectrogram_torch(cpu, *arguments)
    actual = mel_spectrogram_torch(gpu, *arguments)
    assert actual.device == device
    expected.square().mean().backward()
    actual.square().mean().backward()
    torch.testing.assert_close(actual.cpu(), expected, rtol=1e-4, atol=1e-5)
    torch.testing.assert_close(gpu.grad.cpu(), cpu.grad, rtol=2e-3, atol=1e-5)


@pytest.mark.skipif(
    importlib.util.find_spec("torch_directml") is None, reason="Separate DirectML runtime required"
)
def test_directml_relative_attention_backward_matches_cpu():
    import copy
    import torch_directml

    if torch_directml.device_count() == 0:
        pytest.skip("No DirectML adapter")
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine/rvc"))
    from infer.module.attentions import MultiHeadAttention

    torch.manual_seed(21)
    cpu = MultiHeadAttention(192, 192, 2, window_size=10)
    gpu = copy.deepcopy(cpu).to(torch_directml.device())
    signal = torch.randn(1, 192, 158)
    gpu_signal = signal.to(torch_directml.device())
    expected = cpu(signal, signal)
    actual = gpu(gpu_signal, gpu_signal)
    expected.square().mean().backward()
    actual.square().mean().backward()
    torch.testing.assert_close(actual.cpu(), expected, rtol=1e-3, atol=1e-5)
    torch.testing.assert_close(gpu.emb_rel_v.grad.cpu(), cpu.emb_rel_v.grad, rtol=1e-3, atol=1e-5)
