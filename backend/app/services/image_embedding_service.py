from __future__ import annotations

from typing import List

import cv2
import numpy as np

TARGET_SIZE = 64


def _l2_normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Zero-norm vector")
    return vector / norm


def generate_embedding_from_bgr(image_bgr: np.ndarray) -> List[float]:
    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("Invalid image")

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (TARGET_SIZE, TARGET_SIZE), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY).astype(np.float32)

    pooled_gray = []
    pooled_grad = []
    for y in range(0, TARGET_SIZE, 4):
        for x in range(0, TARGET_SIZE, 4):
            patch = gray[y : y + 4, x : x + 4]
            gy, gx = np.gradient(patch)
            grad = np.sqrt((gx * gx) + (gy * gy))
            pooled_gray.append(float(np.mean(patch) / 255.0))
            pooled_grad.append(float(np.mean(grad) / 255.0))

    vector = np.array([*pooled_gray, *pooled_grad], dtype=np.float32)
    normalized = _l2_normalize(vector)
    return normalized.tolist()
