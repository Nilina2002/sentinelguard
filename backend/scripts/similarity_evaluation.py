import os
from typing import List

import cv2
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
)

from deepface import DeepFace


# =========================================================
# CONFIG
# =========================================================

LFW_DIR = "lfw/lfw-deepfunneled/lfw-deepfunneled"

PAIRS_CSV = "lfw/pairs.csv"

HANDCRAFTED_THRESHOLD = 0.82

DEEPFACE_MODEL = "ArcFace"

TARGET_SIZE = 64
EMBEDDING_DIM = 512


# =========================================================
# HANDCRAFTED SYSTEM
# =========================================================

def l2_normalize(vector: np.ndarray) -> np.ndarray:

    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector

    return vector / norm


def average_vectors(vectors: List[np.ndarray]) -> np.ndarray:

    return np.mean(vectors, axis=0)


def draw_transformed(
    image: np.ndarray,
    mode: str,
) -> np.ndarray:

    resized = cv2.resize(
        image,
        (TARGET_SIZE, TARGET_SIZE)
    )

    if mode == "flip":

        return cv2.flip(resized, 1)

    if mode == "centerCrop":

        h, w = image.shape[:2]

        side = min(h, w)

        sx = (w - side) // 2
        sy = (h - side) // 2

        cropped = image[
            sy:sy + side,
            sx:sx + side
        ]

        return cv2.resize(
            cropped,
            (TARGET_SIZE, TARGET_SIZE)
        )

    if mode == "brightened":

        bright = cv2.convertScaleAbs(
            resized,
            alpha=1.05,
            beta=4
        )

        return bright

    return resized


def compute_descriptor(
    image: np.ndarray
) -> np.ndarray:

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = gray.astype(np.float32)

    pooled_gray = []
    pooled_grad = []

    for y in range(0, TARGET_SIZE, 4):

        for x in range(0, TARGET_SIZE, 4):

            block = gray[
                y:y+4,
                x:x+4
            ]

            gx = cv2.Sobel(
                block,
                cv2.CV_32F,
                1,
                0,
                ksize=3
            )

            gy = cv2.Sobel(
                block,
                cv2.CV_32F,
                0,
                1,
                ksize=3
            )

            grad = np.sqrt(gx**2 + gy**2)

            pooled_gray.append(
                np.mean(block) / 255.0
            )

            pooled_grad.append(
                np.mean(grad) / 255.0
            )

    vector = np.array(
        pooled_gray + pooled_grad,
        dtype=np.float32
    )

    if len(vector) != EMBEDDING_DIM:

        raise ValueError(
            f"Embedding size mismatch: {len(vector)}"
        )

    return l2_normalize(vector)


def generate_handcrafted_embedding(
    image_path: str
) -> np.ndarray:

    image = cv2.imread(image_path)

    if image is None:

        raise ValueError(
            f"Could not load image: {image_path}"
        )

    views = [
        "original",
        "flip",
        "centerCrop",
        "brightened",
    ]

    descriptors = []

    for mode in views:

        transformed = draw_transformed(
            image,
            mode
        )

        descriptor = compute_descriptor(
            transformed
        )

        descriptors.append(descriptor)

    embedding = average_vectors(descriptors)

    return l2_normalize(embedding)


# =========================================================
# IMAGE PATH HELPER
# =========================================================

def build_image_path(
    person_name: str,
    image_num: int
) -> str:

    filename = (
        f"{person_name}_{image_num:04d}.jpg"
    )

    return os.path.join(
        LFW_DIR,
        person_name,
        filename
    )


# =========================================================
# LOAD OFFICIAL LFW PAIRS
# =========================================================

print("Loading LFW pairs...")

pairs = []

with open(
    PAIRS_CSV,
    "r",
    encoding="utf-8"
) as f:

    lines = f.readlines()

for line in lines:

    line = line.strip()

    if not line:
        continue

    parts = line.split(",")

    parts = [
        p.strip()
        for p in parts
        if p.strip()
    ]

    # skip header row
    if parts[0].lower() in [
        "name",
        "name1",
    ]:
        continue

    try:

        # =================================================
        # GENUINE PAIR
        # person, img1, img2
        # =================================================

        if len(parts) == 3:

            person = parts[0]

            img1_num = int(parts[1])
            img2_num = int(parts[2])

            path1 = build_image_path(
                person,
                img1_num
            )

            path2 = build_image_path(
                person,
                img2_num
            )

            pairs.append(
                (
                    path1,
                    path2,
                    1,
                )
            )

        # =================================================
        # IMPOSTOR PAIR
        # person1, img1, person2, img2
        # =================================================

        elif len(parts) == 4:

            person1 = parts[0]
            img1_num = int(parts[1])

            person2 = parts[2]
            img2_num = int(parts[3])

            path1 = build_image_path(
                person1,
                img1_num
            )

            path2 = build_image_path(
                person2,
                img2_num
            )

            pairs.append(
                (
                    path1,
                    path2,
                    0,
                )
            )

    except Exception:

        print(
            f"Skipping malformed line: {line}"
        )

all_pairs = pairs

print(
    f"Loaded evaluation pairs: "
    f"{len(all_pairs)}"
)


# =========================================================
# UNIQUE IMAGE PATHS
# =========================================================

all_unique_paths = set()

for path1, path2, _ in all_pairs:

    all_unique_paths.add(path1)
    all_unique_paths.add(path2)

print(
    f"Unique images: "
    f"{len(all_unique_paths)}"
)


# =========================================================
# GENERATE HANDCRAFTED EMBEDDINGS
# =========================================================

print("\nGenerating handcrafted embeddings...")

handcrafted_embeddings = {}

for idx, path in enumerate(all_unique_paths):

    try:

        embedding = (
            generate_handcrafted_embedding(path)
        )

        handcrafted_embeddings[path] = embedding

    except Exception:

        print(
            f"Failed handcrafted: {path}"
        )

    if idx % 100 == 0:

        print(
            f"Processed "
            f"{idx}/{len(all_unique_paths)}"
        )

print(
    f"\nHandcrafted embeddings generated: "
    f"{len(handcrafted_embeddings)}"
)


# =========================================================
# GENERATE DEEPFACE EMBEDDINGS
# =========================================================

print("\nGenerating DeepFace embeddings...")

deepface_embeddings = {}

for idx, path in enumerate(all_unique_paths):

    try:

        embedding_obj = DeepFace.represent(
            img_path=path,
            model_name=DEEPFACE_MODEL,
            detector_backend="opencv",
            enforce_detection=False,
        )

        embedding = np.array(
            embedding_obj[0]["embedding"],
            dtype=np.float32
        )

        embedding = l2_normalize(embedding)

        deepface_embeddings[path] = embedding

    except Exception:

        print(
            f"Failed DeepFace: {path}"
        )

    if idx % 100 == 0:

        print(
            f"Processed "
            f"{idx}/{len(all_unique_paths)}"
        )

print(
    f"\nDeepFace embeddings generated: "
    f"{len(deepface_embeddings)}"
)


# =========================================================
# THRESHOLD SWEEP FOR DEEPFACE
# =========================================================

print("\nTesting thresholds for ArcFace...\n")

best_acc = 0
best_threshold = 0

for threshold in np.arange(0.1, 1.0, 0.01):

    y_true = []
    y_pred = []

    for path1, path2, label in all_pairs:

        if path1 not in deepface_embeddings:
            continue

        if path2 not in deepface_embeddings:
            continue

        emb1 = deepface_embeddings[path1]
        emb2 = deepface_embeddings[path2]

        similarity = float(
            np.dot(emb1, emb2)
        )

        prediction = (
            1 if similarity >= threshold else 0
        )

        y_true.append(label)
        y_pred.append(prediction)

    acc = accuracy_score(
        y_true,
        y_pred
    )

    if acc > best_acc:

        best_acc = acc
        best_threshold = threshold

print(
    f"Best ArcFace threshold: "
    f"{best_threshold:.2f}"
)

print(
    f"Best ArcFace accuracy : "
    f"{best_acc:.4f}"
)


# =========================================================
# EVALUATION FUNCTION
# =========================================================

def evaluate_system(
    embeddings,
    threshold,
    system_name,
):

    print("\n=================================")
    print(f"EVALUATING: {system_name}")
    print("=================================")

    y_true = []
    y_pred = []
    y_scores = []

    skipped = 0

    for path1, path2, label in all_pairs:

        if path1 not in embeddings:
            skipped += 1
            continue

        if path2 not in embeddings:
            skipped += 1
            continue

        emb1 = embeddings[path1]
        emb2 = embeddings[path2]

        similarity = float(
            np.dot(emb1, emb2)
        )

        prediction = (
            1 if similarity >= threshold else 0
        )

        y_true.append(label)
        y_pred.append(prediction)
        y_scores.append(similarity)

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred
    )

    recall = recall_score(
        y_true,
        y_pred
    )

    f1 = f1_score(
        y_true,
        y_pred
    )

    auc = roc_auc_score(
        y_true,
        y_scores
    )

    cm = confusion_matrix(
        y_true,
        y_pred
    )

    tn, fp, fn, tp = cm.ravel()

    far = fp / (fp + tn)
    frr = fn / (fn + tp)

    print(f"\nPairs evaluated: {len(y_true)}")
    print(f"Skipped pairs: {skipped}")

    print(f"\nAccuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print(f"ROC AUC   : {auc:.4f}")

    print(f"\nFAR: {far:.4f}")
    print(f"FRR: {frr:.4f}")

    print("\nConfusion Matrix:")
    print(cm)

    return {
        "System": system_name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "AUC": auc,
        "FAR": far,
        "FRR": frr,
    }


# =========================================================
# RUN EVALUATIONS
# =========================================================

handcrafted_results = evaluate_system(
    handcrafted_embeddings,
    HANDCRAFTED_THRESHOLD,
    "Handcrafted System",
)

deepface_results = evaluate_system(
    deepface_embeddings,
    best_threshold,
    f"DeepFace ({DEEPFACE_MODEL})",
)


# =========================================================
# FINAL RESULTS
# =========================================================

print("\n=================================")
print("FINAL RESULTS")
print("=================================")

results_df = pd.DataFrame([
    handcrafted_results,
    deepface_results,
])

print(results_df)
