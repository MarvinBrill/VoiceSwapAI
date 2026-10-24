import numpy as np


def retrieve_features(index, vectors, features):
    distances, neighbors = index.search(features, k=8)
    valid = (neighbors >= 0) & np.isfinite(distances)
    weights = np.where(valid, np.square(1 / np.maximum(distances, 1e-6)), 0)
    total = weights.sum(axis=1, keepdims=True)
    weights /= np.maximum(total, 1e-12)
    retrieved = np.sum(vectors[np.maximum(neighbors, 0)] * weights[..., None], axis=1)
    return np.where(total > 0, retrieved, features)
