import shutil
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
import soundfile as sf

from app import conversion
from app.schemas import ConversionRequest


@pytest.mark.parametrize("separate", [False, True])
@pytest.mark.parametrize("gain", [-24, -6, 0, 6, 12])
def test_voice_gain_in_export_preserves_backing_and_prevents_clipping(tmp_path, monkeypatch, separate, gain):
    rate = 44100
    # Cross a processing boundary and include a loud peak to exercise the file-wide protection.
    vocals = np.full(rate * 31, 0.1, dtype=np.float32)
    vocals[rate] = 0.4
    source = tmp_path / "source.wav"
    sf.write(source, np.column_stack([vocals, vocals]), rate, subtype="FLOAT")
    (tmp_path / "outputs").mkdir()
    monkeypatch.setattr(conversion, "DATA", tmp_path)
    monkeypatch.setattr(conversion, "data_path", lambda path: tmp_path / path)
    monkeypatch.setattr(conversion, "ensure_assets", lambda *args: None)
    monkeypatch.setattr(conversion, "decode", lambda src, dst, *args, **kwargs: shutil.copyfile(src, dst))
    monkeypatch.setattr(conversion, "encode", lambda src, dst, *args: shutil.copyfile(src, dst))
    converter = SimpleNamespace(
        sample_rate=rate, config=SimpleNamespace(device="cpu"),
        convert=lambda audio, *args: audio[:, 0],
    )
    monkeypatch.setattr(conversion, "VoiceConverter", lambda model: converter)
    separator = SimpleNamespace(separate=lambda audio: (audio, np.full_like(audio, 0.05)))
    monkeypatch.setattr(conversion, "VocalSeparator", lambda device: separator)
    store = Mock()
    store.get.side_effect = [{"name": "Voice"}, {"name": "Audio.wav", "path": "source.wav"}]
    options = ConversionRequest(
        audio_ids=["audio"], model_id="model", vocal_gain=gain, separate_vocals=separate,
    ).model_dump()

    result = conversion.run_conversion(store, {"id": "gain-test", "parameters": options}, Mock())
    actual, actual_rate = sf.read(tmp_path / result["outputs"][0]["path"])

    expected = vocals * 10 ** (gain / 20) + (0.05 if separate else 0)
    expected /= max(1, np.max(np.abs(expected)) / 0.98)
    assert actual_rate == rate
    assert actual.shape == (len(vocals), 2)
    assert np.max(np.abs(actual)) <= 0.980001
    np.testing.assert_allclose(actual[:, 0], expected, atol=2e-7)
    np.testing.assert_allclose(actual[:, 1], expected, atol=2e-7)
