import os
import random
import itertools
import pandas as pd
import numpy as np
import face_recognition

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    classification_report
)

# =========================
# CONFIG
# =========================

IMAGE_FOLDER = "dataset/faces"
CSV_PATH = "dataset/labels.csv"

TOLERANCE = 0.6

# =========================
# LOAD CSV
# =========================

df = pd.read_csv(CSV_PATH)

# =========================
# BUILD LABEL GROUPS
# =========================

label_groups = {}

for _, row in df.iterrows():
    label = row["label"]
    image_name = row["id"]

    label_groups.setdefault(label, []).append(image_name)

# =========================
# PRECOMPUTE EMBEDDINGS
# =========================

print("Generating embeddings...")

embeddings = {}
failed_images = []

for image_name in df["id"].unique():

    path = os.path.join(IMAGE_FOLDER, image_name)

    try:
        image = face_recognition.load_image_file(path)

        encodings = face_recognition.face_encodings(image)

        if len(encodings) == 0:
            failed_images.append(image_name)
            continue

        embeddings[image_name] = encodings[0]

    except Exception as e:
        print(f"Error processing {image_name}: {e}")

print(f"Embeddings generated: {len(embeddings)}")
print(f"Failed images: {len(failed_images)}")

# =========================
# CREATE GENUINE PAIRS
# =========================

genuine_pairs = []

for label, images in label_groups.items():

    valid_images = [img for img in images if img in embeddings]

    if len(valid_images) >= 2:

        pairs = list(itertools.combinations(valid_images, 2))

        for p in pairs:
            genuine_pairs.append((p[0], p[1], 1))

# =========================
# CREATE IMPOSTOR PAIRS
# =========================

all_labels = list(label_groups.keys())

impostor_pairs = []

for _ in range(len(genuine_pairs)):

    l1, l2 = random.sample(all_labels, 2)

    img1 = random.choice(label_groups[l1])
    img2 = random.choice(label_groups[l2])

    if img1 in embeddings and img2 in embeddings:
        impostor_pairs.append((img1, img2, 0))

# =========================
# MERGE PAIRS
# =========================

all_pairs = genuine_pairs + impostor_pairs

random.shuffle(all_pairs)

# =========================
# EVALUATION
# =========================

y_true = []
y_pred = []
y_scores = []

print("Running comparisons...")

for img1_name, img2_name, label in all_pairs:

    enc1 = embeddings[img1_name]
    enc2 = embeddings[img2_name]

    distance = face_recognition.face_distance(
        [enc1],
        enc2
    )[0]

    similarity = 1 - distance

    prediction = 1 if distance < TOLERANCE else 0

    y_true.append(label)
    y_pred.append(prediction)
    y_scores.append(similarity)

# =========================
# METRICS
# =========================

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)

cm = confusion_matrix(y_true, y_pred)

auc = roc_auc_score(y_true, y_scores)

tn, fp, fn, tp = cm.ravel()

far = fp / (fp + tn)
frr = fn / (fn + tp)

# =========================
# RESULTS
# =========================

print("\n========== RESULTS ==========")

print(f"Total pairs tested: {len(y_true)}")

print(f"\nAccuracy  : {accuracy:.4f}")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1 Score  : {f1:.4f}")
print(f"ROC AUC   : {auc:.4f}")

print(f"\nFAR (False Accept Rate): {far:.4f}")
print(f"FRR (False Reject Rate): {frr:.4f}")

print("\nConfusion Matrix:")
print(cm)

print("\nClassification Report:")
print(classification_report(y_true, y_pred))
