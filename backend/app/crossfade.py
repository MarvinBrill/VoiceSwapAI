import numpy as np


class CrossfadeWriter:
    """Write context-overlapping blocks without duplicating timeline samples."""

    def __init__(self, writers, overlap):
        self.writers = writers
        self.overlap = overlap
        self.tails = None

    def write(self, blocks, final=False):
        for index, (writer, block) in enumerate(zip(self.writers, blocks, strict=True)):
            if self.tails is not None:
                previous = self.tails[index]
                fade = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, len(previous)))).astype(np.float32)
                if block.ndim == 2:
                    fade = fade[:, None]
                writer.write(previous * (1 - fade) + block[: len(previous)] * fade)
                block = block[len(previous) :]
            if final:
                writer.write(block)
            else:
                writer.write(block[: -self.overlap])
        self.tails = None if final else [block[-self.overlap :].copy() for block in blocks]
