import os
import random
import itertools
import pandas as pd
import numpy as np
import face_recognition
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    classification_report,
    roc_curve
)

# =========================
# CONFIG
# =========================

IMAGE_FOLDER = "dataset/faces"
CSV_PATH = "dataset/labels.csv"

TOLERANCE = 0.6

# Folder to save result images
RESULTS_FOLDER = "results/face_recognition_evaluation"
os.makedirs(RESULTS_FOLDER, exist_ok=True)

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

while len(impostor_pairs) < len(genuine_pairs):

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

genuine_scores = []
impostor_scores = []

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

    if label == 1:
        genuine_scores.append(similarity)
    else:
        impostor_scores.append(similarity)

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

# =========================
# SAVE METRICS TABLE
# =========================

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

# Format values to 4 decimal places
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

plt.title("Face Recognition Evaluation Metrics", fontsize=14)

metrics_path = os.path.join(
    RESULTS_FOLDER,
    "metrics_table.png"
)

plt.savefig(metrics_path, bbox_inches='tight')
plt.close()


# =========================
# ROC CURVE
# =========================

fpr, tpr, thresholds = roc_curve(y_true, y_scores)

plt.figure(figsize=(6, 5))

plt.plot(fpr, tpr, label=f"AUC = {auc:.4f}")
plt.plot([0, 1], [0, 1], linestyle='--')

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")
plt.legend()

roc_path = os.path.join(RESULTS_FOLDER, "roc_curve.png")

plt.savefig(roc_path, bbox_inches='tight')
plt.close()

# =========================
# SIMILARITY DISTRIBUTION
# =========================

plt.figure(figsize=(8, 5))

plt.hist(
    genuine_scores,
    bins=30,
    alpha=0.6,
    label="Genuine Pairs"
)

plt.hist(
    impostor_scores,
    bins=30,
    alpha=0.6,
    label="Impostor Pairs"
)

plt.axvline(
    x=(1 - TOLERANCE),
    linestyle='--',
    label='Threshold'
)

plt.xlabel("Similarity Score")
plt.ylabel("Frequency")
plt.title("Similarity Score Distribution")
plt.legend()

dist_path = os.path.join(RESULTS_FOLDER, "similarity_distribution.png")

plt.savefig(dist_path, bbox_inches='tight')
plt.close()

# =========================
# BAR CHART OF METRICS
# =========================

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

bars = plt.bar(metric_names, metric_values)

plt.ylim(0, 1)

for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,
        yval + 0.01,
        f"{yval:.3f}",
        ha='center'
    )

plt.title("Performance Metrics")

bar_path = os.path.join(RESULTS_FOLDER, "metrics_bar_chart.png")

plt.savefig(bar_path, bbox_inches='tight')
plt.close()

# =========================
# FINAL MESSAGE
# =========================

print("\nSaved Result Images:")
print(metrics_path)
print(roc_path)
print(dist_path)
print(bar_path)
