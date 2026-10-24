import sys

import numpy as np
from scipy.io import wavfile

from app.settings import ENGINE

sys.path.insert(0, str(ENGINE))
from train.utils import load_wav_to_torch


def test_integer_and_float_wavs_have_same_training_amplitude(tmp_path):
    expected = np.array([-0.5, 0, 0.25, 0.5], dtype=np.float32)
    pcm = tmp_path / "pcm.wav"
    floating = tmp_path / "float.wav"
    wavfile.write(pcm, 40000, (expected * 32768).astype(np.int16))
    wavfile.write(floating, 40000, expected)
    pcm_samples, rate = load_wav_to_torch(pcm)
    float_samples, _ = load_wav_to_torch(floating)
    assert rate == 40000
    np.testing.assert_array_equal(pcm_samples.numpy(), expected)
    np.testing.assert_array_equal(pcm_samples.numpy(), float_samples.numpy())
