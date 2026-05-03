import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    ENV: str = os.getenv("ENV", "dev")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecret")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    # Defaults tuned for real-world lighting/pose variance; override via env in production.
    SELFIE_FACE_THRESHOLD: float = float(os.getenv("SELFIE_FACE_THRESHOLD", "0.52"))
    SUPPORT_REPORT_THRESHOLD: float = float(os.getenv("SUPPORT_REPORT_THRESHOLD", "0.84"))
    SUPPORT_DB_THRESHOLD: float = float(os.getenv("SUPPORT_DB_THRESHOLD", "0.78"))
    FINAL_THRESHOLD: float = float(os.getenv("FINAL_THRESHOLD", "0.75"))
    SELFIE_LIVENESS_THRESHOLD: float = float(os.getenv("SELFIE_LIVENESS_THRESHOLD", "70.0"))

settings = Settings()