import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session, select
from app.api.deps import get_db
from app.models.image import Image

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/upload")
def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image = Image(user_id=1, image_url=file_path)  # temp user_id=1
    db.add(image)
    db.commit()
    db.refresh(image)

    return image


@router.get("/")
def get_images(db: Session = Depends(get_db)):
    images = db.exec(select(Image).where(Image.is_deleted == False)).all()
    return images


@router.delete("/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db)):
    image = db.get(Image, image_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image.is_deleted = True
    db.commit()

    return {"message": "Image deleted"}
