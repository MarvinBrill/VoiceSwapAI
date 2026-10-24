import sys

import numpy as np

from app.settings import ENGINE

sys.path.insert(0, str(ENGINE))
from infer.vc.retrieval import retrieve_features


def test_exact_index_matches_and_missing_neighbors_stay_finite():
    vectors = np.array([[1, 2], [9, 9]], dtype=np.float32)
    features = np.array([[3, 4], [5, 6]], dtype=np.float32)

    class Index:
        def search(self, features, k):
            return np.array([[0, np.inf], [np.inf, np.inf]], dtype=np.float32), np.array([[0, -1], [-1, -1]])

    result = retrieve_features(Index(), vectors, features)
    np.testing.assert_array_equal(result[0], vectors[0])
    np.testing.assert_array_equal(result[1], features[1])
    assert np.isfinite(result).all()
