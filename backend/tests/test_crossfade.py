import numpy as np

from app.crossfade import CrossfadeWriter


class Buffer:
    def __init__(self):
        self.chunks = []

    def write(self, samples):
        self.chunks.append(samples.copy())


def test_overlapping_chunks_preserve_timeline_and_stereo():
    mono, stereo = Buffer(), Buffer()
    writer = CrossfadeWriter([mono, stereo], overlap=10)
    original = np.arange(205, dtype=np.float32)
    for start in (0, 100, 200):
        end = min(start + 100, 205)
        chunk = original[max(0, start - 10) : end]
        writer.write([chunk, np.stack([chunk, chunk], axis=1)], final=end == 205)
    np.testing.assert_allclose(np.concatenate(mono.chunks), original, atol=0.0001)
    assert np.concatenate(stereo.chunks).shape == (205, 2)


def test_crossfade_smooths_a_boundary_discontinuity():
    mono = Buffer()
    writer = CrossfadeWriter([mono], overlap=10)
    writer.write([np.zeros(100, dtype=np.float32)])
    writer.write([np.ones(110, dtype=np.float32)], final=True)
    samples = np.concatenate(mono.chunks)
    assert len(samples) == 200
    assert np.max(np.abs(np.diff(samples))) < 0.2
