import random

def generate_embedding(image_url: str):
    return {
        "vector_id": f"vec_{random.randint(1000,9999)}",
        "embedding": [0.1, 0.2]  # mock
    }


def search_similar(embedding):
    return [
        {"image_id": 1, "score": 0.95},
        {"image_id": 2, "score": 0.93},
    ]
