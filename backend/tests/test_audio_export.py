import json
import shutil
import subprocess

import numpy as np
import pytest
import soundfile as sf

from app.audio import decode, encode, probe


pytestmark = pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="Audio export integration tests require FFmpeg and FFprobe",
)


@pytest.mark.parametrize(
    "suffix,requested_rate,expected_rate",
    [
        ("mp3", 0, 44100),
        ("mp3", 32000, 32000),
        ("mp3", 40000, 44100),
        ("mp3", 44100, 44100),
        ("mp3", 48000, 48000),
        ("wav", 40000, 40000),
        ("flac", 40000, 40000),
    ],
)
def test_export_encodes_playable_stereo_audio(tmp_path, suffix, requested_rate, expected_rate):
    # Use Windows paths with spaces and Unicode, as in real user installations.
    folder = tmp_path / "Meine Audios ä"
    folder.mkdir()
    source = folder / "normalized.wav"
    destination = folder / f"result.{suffix}"
    time = np.arange(44100) / 44100
    samples = np.column_stack([0.2 * np.sin(2 * np.pi * frequency * time) for frequency in (220, 440)])
    sf.write(source, samples, 44100, subtype="PCM_24")

    encode(source, destination, requested_rate)

    info = probe(destination)
    assert info["sample_rate"] == expected_rate
    assert info["channels"] == 2
    assert info["duration"] == pytest.approx(1, abs=0.1)
    decoded = folder / "decoded.wav"
    decode(destination, decoded, 44100, channels=2)
    actual, _ = sf.read(decoded)
    assert abs(len(actual) - len(samples)) <= 2
    assert np.isfinite(actual).all()
    np.testing.assert_allclose(
        np.sqrt(np.mean(actual ** 2, axis=0)),
        np.sqrt(np.mean(samples ** 2, axis=0)),
        rtol=0.05,
    )
    if suffix == "mp3":
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(destination)],
            check=True, capture_output=True, text=True,
        )
        stream = json.loads(result.stdout)["streams"][0]
        assert stream["codec_name"] == "mp3"
        assert int(stream["bit_rate"]) == 320000


def test_failed_export_reports_ffmpeg_details(tmp_path):
    with pytest.raises(RuntimeError) as error:
        encode(tmp_path / "missing.wav", tmp_path / "result.mp3", 40000)
    assert "Audioexport (MP3) fehlgeschlagen" in str(error.value)
    assert "missing.wav" in str(error.value)
