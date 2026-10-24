import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine/rvc"))
from infer.module.models import SineGen


@pytest.fixture(params=["cpu", "cuda", "directml"])
def device(request):
    if request.param == "cuda":
        if not torch.cuda.is_available():
            pytest.skip("CUDA runtime and adapter required")
        return torch.device("cuda:0")
    if request.param == "directml":
        if importlib.util.find_spec("torch_directml") is None:
            pytest.skip("Separate DirectML runtime required")
        import torch_directml

        if not torch_directml.device_count():
            pytest.skip("DirectML adapter required")
        return torch_directml.device()
    return torch.device("cpu")


@pytest.mark.parametrize("rate", [32000, 40000, 48000])
@pytest.mark.parametrize("seconds", [1, 32])
def test_voice_source_follows_pitch_over_a_full_conversion_chunk(device, rate, seconds):
    pitch = 200 + 80 * np.sin(np.arange(seconds * 100, dtype=np.float32) * 0.017)
    # Independent phase reference: each pitch frame spans 10 ms of audio.
    frequencies = np.repeat(pitch.astype(np.float64), rate // 100)
    expected = np.sin(2 * np.pi * np.cumsum(frequencies / rate))
    generator = SineGen(rate)

    actual = generator._f02sine(torch.from_numpy(pitch).reshape(1, -1, 1).to(device), rate // 100)

    assert actual.device == device
    actual = actual.cpu().numpy().ravel()
    assert actual.shape == (rate * seconds,)
    assert np.sqrt(np.mean((actual - expected) ** 2)) < 0.002
    assert np.max(np.abs(actual - expected)) < 0.01


def test_harmonic_multipliers_match_reference(device, monkeypatch):
    # Fix the random harmonic starting phases so backend outputs are comparable.
    monkeypatch.setattr(torch, "rand", lambda *args, **kwargs: torch.zeros(*args, **kwargs))
    pitch = torch.full((1, 100, 1), 220.0)
    generator = SineGen(40000, harmonic_num=2)
    expected = generator._f02sine(pitch, 400)
    actual = generator._f02sine(pitch.to(device), 400)
    torch.testing.assert_close(actual.cpu(), expected, rtol=0, atol=0.002)
