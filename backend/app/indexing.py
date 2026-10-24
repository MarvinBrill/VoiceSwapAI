"""FAISS index builder in its own process, avoiding Windows OpenMP conflicts."""

import argparse
from pathlib import Path

import faiss
import numpy as np


def build_index(folder, destination):
    # Keep a bounded, unbiased sample while training still uses all features.
    rng = np.random.default_rng(42)
    vectors = np.empty((0, 768), dtype=np.float32)
    priorities = np.empty(0)
    for path in sorted((folder / "3_feature768").glob("*.npy")):
        current = np.load(path, allow_pickle=False)
        vectors = np.concatenate((vectors, current))
        priorities = np.concatenate((priorities, rng.random(len(current))))
        if len(vectors) > 200000:
            keep = np.argpartition(priorities, -200000)[-200000:]
            vectors, priorities = vectors[keep], priorities[keep]
    if len(vectors) < 8:
        raise ValueError("Zu wenige Merkmale für einen Stimmenindex.")
    print(f"Stimmenindex: {len(vectors):,} Merkmale", flush=True)
    clusters = min(int(16 * np.sqrt(len(vectors))), len(vectors) // 39)
    if clusters < 2:
        index = faiss.IndexFlatL2(768)
    else:
        index = faiss.index_factory(768, f"IVF{clusters},Flat")
        index.train(vectors)
        index.nprobe = 1
    index.add(vectors)
    faiss.write_index(index, str(destination))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("destination", type=Path)
    options = parser.parse_args()
    build_index(options.folder, options.destination)
