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
    roc_curve
)
from deepface import DeepFace
import matplotlib.pyplot as plt
import seaborn as sns


# =========================================================
# CONFIG
# =========================================================

LFW_DIR = "lfw/lfw-deepfunneled/lfw-deepfunneled"
PAIRS_CSV = "lfw/pairs.csv"
HANDCRAFTED_THRESHOLD = 0.82
DEEPFACE_MODEL = "ArcFace"
TARGET_SIZE = 64
EMBEDDING_DIM = 512
RESULTS_FOLDER = "results/similarity_evaluation"

os.makedirs(RESULTS_FOLDER, exist_ok=True)


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

    genuine_scores = []
    impostor_scores = []

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

        if label == 1:
            genuine_scores.append(similarity)
        else:
            impostor_scores.append(similarity)

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

    # =====================================================
    # SAVE METRICS TABLE
    # =====================================================

    metrics_df = pd.DataFrame({
        "Metric": [
            "Accuracy",
            "Precision",
            "Recall",
            "F1 Score",
            "ROC AUC",
            "FAR",
            "FRR"
        ],
        "Value": [
            accuracy,
            precision,
            recall,
            f1,
            auc,
            far,
            frr
        ]
    })

    # Convert values to formatted strings
    table_data = [
        [row["Metric"], f"{row['Value']:.4f}"]
        for _, row in metrics_df.iterrows()
    ]

    plt.figure(figsize=(8, 4))
    plt.axis('off')

    table = plt.table(
        cellText=table_data,
        colLabels=metrics_df.columns,
        loc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.8)

    plt.title(f"{system_name} Metrics")

    plt.savefig(
        os.path.join(
            RESULTS_FOLDER,
            f"{system_name}_metrics_table.png"
        ),
        bbox_inches='tight'
    )

    plt.close()

    # =====================================================
    # CONFUSION MATRIX
    # =====================================================

    plt.figure(figsize=(6, 5))

    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=["Impostor", "Genuine"],
        yticklabels=["Impostor", "Genuine"]
    )

    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"{system_name} Confusion Matrix")

    plt.savefig(
        os.path.join(
            RESULTS_FOLDER,
            f"{system_name}_confusion_matrix.png"
        ),
        bbox_inches='tight'
    )

    plt.close()

    # =====================================================
    # ROC CURVE
    # =====================================================

    fpr, tpr, _ = roc_curve(
        y_true,
        y_scores
    )

    plt.figure(figsize=(6, 5))

    plt.plot(
        fpr,
        tpr,
        label=f"AUC = {auc:.4f}"
    )

    plt.plot(
        [0, 1],
        [0, 1],
        linestyle='--'
    )

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"{system_name} ROC Curve")
    plt.legend()

    plt.savefig(
        os.path.join(
            RESULTS_FOLDER,
            f"{system_name}_roc_curve.png"
        ),
        bbox_inches='tight'
    )

    plt.close()

    # =====================================================
    # SIMILARITY DISTRIBUTION
    # =====================================================

    plt.figure(figsize=(8, 5))

    plt.hist(
        genuine_scores,
        bins=30,
        alpha=0.6,
        label="Genuine"
    )

    plt.hist(
        impostor_scores,
        bins=30,
        alpha=0.6,
        label="Impostor"
    )

    plt.axvline(
        x=threshold,
        linestyle='--',
        label='Threshold'
    )

    plt.xlabel("Similarity Score")
    plt.ylabel("Frequency")
    plt.title(f"{system_name} Similarity Distribution")
    plt.legend()

    plt.savefig(
        os.path.join(
            RESULTS_FOLDER,
            f"{system_name}_distribution.png"
        ),
        bbox_inches='tight'
    )

    plt.close()

    # =====================================================
    # METRIC BAR CHART
    # =====================================================

    metric_names = [
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "AUC"
    ]

    metric_values = [
        accuracy,
        precision,
        recall,
        f1,
        auc
    ]

    plt.figure(figsize=(8, 5))

    bars = plt.bar(
        metric_names,
        metric_values
    )

    plt.ylim(0, 1)

    for bar in bars:

        yval = bar.get_height()

        plt.text(
            bar.get_x() + bar.get_width()/2,
            yval + 0.01,
            f"{yval:.3f}",
            ha='center'
        )

    plt.title(f"{system_name} Performance Metrics")

    plt.savefig(
        os.path.join(
            RESULTS_FOLDER,
            f"{system_name}_bar_chart.png"
        ),
        bbox_inches='tight'
    )

    plt.close()

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

# =========================================================
# FINAL COMPARISON CHART
# =========================================================

comparison_metrics = [
    "Accuracy",
    "Precision",
    "Recall",
    "F1",
    "AUC"
]

x = np.arange(len(comparison_metrics))
width = 0.35

handcrafted_values = [
    handcrafted_results[m]
    for m in comparison_metrics
]

deepface_values = [
    deepface_results[m]
    for m in comparison_metrics
]

plt.figure(figsize=(10, 6))

plt.bar(
    x - width/2,
    handcrafted_values,
    width,
    label="Handcrafted"
)

plt.bar(
    x + width/2,
    deepface_values,
    width,
    label="ArcFace"
)

plt.xticks(
    x,
    comparison_metrics
)

plt.ylim(0, 1)

plt.ylabel("Score")
plt.title("System Performance Comparison")

plt.legend()

plt.savefig(
    os.path.join(
        RESULTS_FOLDER,
        "final_system_comparison.png"
    ),
    bbox_inches='tight'
)

plt.close()

print("\nSaved result images to results/")
