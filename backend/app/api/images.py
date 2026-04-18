import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session, select
from app.api.deps import get_db
from app.models.image import Image
import uuid
from app.api.deps import get_current_user
from app.models import User, EmbeddingMetadata
from app.schemas.common import APIResponse

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/upload")
def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image = Image(user_id=user.id, image_url=file_path)
    db.add(image)
    db.commit()
    db.refresh(image)

    # TODO: create the embedding
    # embedding = generate_embedding(file_path)
    # embedding_meta_data = EmbeddingMetadata(
    #     image_id=image.id,
    #     vector_id=str(uuid.uuid4()),  # placeholder for actual vector ID from ChromaDB
    #     model_used="clip",

    # )
    # db.add(embedding_meta_data)
    # db.commit()
    
    return APIResponse(success=True, message="Image uploaded successfully")

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
