import unittest

import numpy as np

from app.api.reports import compute_final_score
from app.services.ai_service import cosine_similarity, normalize_embedding
from app.services.image_embedding_service import generate_embedding_from_bgr


class OwnershipVerificationTests(unittest.TestCase):
    def test_compute_final_score_uses_lowest_gate_score(self):
        score = compute_final_score([0.91, 0.88, 0.96])
        self.assertEqual(score, 0.88)

    def test_compute_final_score_handles_missing_scores(self):
        score = compute_final_score([None, 0.94, None])
        self.assertEqual(score, 0.94)

    def test_generate_embedding_shape_and_norm(self):
        image = np.full((128, 128, 3), 180, dtype=np.uint8)
        embedding = generate_embedding_from_bgr(image)
        self.assertEqual(len(embedding), 512)
        self.assertAlmostEqual(float(np.linalg.norm(np.array(embedding))), 1.0, places=4)

    def test_cosine_similarity_for_identical_embedding(self):
        vector = normalize_embedding([1.0] * 512)
        score = cosine_similarity(vector, vector)
        self.assertAlmostEqual(score, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
