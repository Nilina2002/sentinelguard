"""
Quick threshold calibration utility for NCII embeddings.

Usage:
    python backend/scripts/calibrate_threshold.py --images-dir backend/uploads
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

TARGET_SIZE = 64


def l2_normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Zero-norm vector")
    return vector / norm


def image_to_embedding(image: Image.Image) -> np.ndarray:
    img = image.convert("RGB").resize((TARGET_SIZE, TARGET_SIZE))
    gray = np.asarray(img.convert("L"), dtype=np.float32)

    pooled_gray: List[float] = []
    pooled_grad: List[float] = []

    for y in range(0, TARGET_SIZE, 4):
        for x in range(0, TARGET_SIZE, 4):
            patch = gray[y : y + 4, x : x + 4]
            gy, gx = np.gradient(patch)
            grad = np.sqrt(gx * gx + gy * gy)
            pooled_gray.append(float(np.mean(patch) / 255.0))
            pooled_grad.append(float(np.mean(grad) / 255.0))

    vector = np.array([*pooled_gray, *pooled_grad], dtype=np.float32)
    return l2_normalize(vector)


def transformed_variants(img: Image.Image) -> List[Image.Image]:
    width, height = img.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2

    cropped = img.crop((left, top, left + side, top + side))
    bright = ImageEnhance.Brightness(img).enhance(1.05)
    return [img, ImageOps.mirror(img), cropped, bright]


def canonical_embedding(img: Image.Image) -> np.ndarray:
    embs = [image_to_embedding(v) for v in transformed_variants(img)]
    stacked = np.stack(embs)
    return l2_normalize(stacked.mean(axis=0))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def load_images(images_dir: Path) -> List[Path]:
    supported = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    return [p for p in images_dir.iterdir() if p.suffix.lower() in supported and p.is_file()]


def evaluate(images_dir: Path) -> Tuple[List[float], List[float]]:
    paths = load_images(images_dir)
    base_embeddings = {}
    for path in paths:
        with Image.open(path) as img:
            base_embeddings[path] = canonical_embedding(img)

    positive_scores: List[float] = []
    negative_scores: List[float] = []

    for path in paths:
        with Image.open(path) as img:
            for variant in transformed_variants(img):
                score = cosine_similarity(base_embeddings[path], canonical_embedding(variant))
                positive_scores.append(score)

    path_list = list(paths)
    for i in range(len(path_list)):
        for j in range(i + 1, len(path_list)):
            negative_scores.append(
                cosine_similarity(base_embeddings[path_list[i]], base_embeddings[path_list[j]])
            )

    return positive_scores, negative_scores


def suggest_threshold(positive: Iterable[float], negative: Iterable[float]) -> float:
    positive = np.array(list(positive), dtype=np.float32)
    negative = np.array(list(negative), dtype=np.float32)

    best_threshold = 0.98
    best_margin = -10.0
    for threshold in np.arange(0.70, 0.99, 0.01):
        tpr = float(np.mean(positive >= threshold)) if len(positive) else 0.0
        fpr = float(np.mean(negative >= threshold)) if len(negative) else 0.0
        margin = tpr - fpr
        if margin > best_margin:
            best_margin = margin
            best_threshold = float(threshold)
    return round(best_threshold, 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-dir", required=True, help="Folder with sample images")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    if not images_dir.exists():
        raise FileNotFoundError(f"Directory not found: {images_dir}")

    positive, negative = evaluate(images_dir)
    threshold = suggest_threshold(positive, negative)

    print(f"Samples: {len(positive)} positive pairs, {len(negative)} negative pairs")
    print(f"Positive mean: {np.mean(positive):.4f}" if positive else "Positive mean: n/a")
    print(f"Negative mean: {np.mean(negative):.4f}" if negative else "Negative mean: n/a")
    print(f"Suggested threshold: {threshold}")


if __name__ == "__main__":
    main()
