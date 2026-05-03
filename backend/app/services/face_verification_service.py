from __future__ import annotations

from dataclasses import dataclass
from typing import List

import cv2
import face_recognition
import numpy as np


@dataclass
class FaceAnalysis:
    encodings: List[np.ndarray]
    face_count: int
    liveness_score: float


def decode_upload_image(file_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image")
    return image


def analyze_faces(image_bgr: np.ndarray) -> FaceAnalysis:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb, model="hog")
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    liveness_score = estimate_liveness(image_bgr)
    return FaceAnalysis(encodings=encodings, face_count=len(encodings), liveness_score=liveness_score)


def estimate_liveness(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    # Low sharpness often indicates screen replay or heavily processed images.
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def best_face_similarity(selfie_encoding: np.ndarray, reported_encodings: List[np.ndarray]) -> float:
    if not reported_encodings:
        return 0.0
    distances = face_recognition.face_distance(reported_encodings, selfie_encoding)
    min_distance = float(np.min(distances))
    return max(0.0, 1.0 - min_distance)
