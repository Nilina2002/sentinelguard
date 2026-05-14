import os
import shutil
import json
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlmodel import Session, select
from sqlalchemy import func, case
from app.api.deps import get_db
from app.models.image import Image
import uuid
from app.api.deps import get_current_user
from app.models import User, EmbeddingMetadata, ImageLike, ImageComment
from app.schemas.common import APIResponse
from app.schemas.image import ImageFeedItem, ImageOwner
from app.schemas.comment import CommentCreate, CommentOut, CommentUser
from app.services.ai_service import is_blocklisted, upsert_image_embedding

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/upload")
def upload_image(
    file: UploadFile = File(...),
    embedding: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        embedding_vector = json.loads(embedding)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid embedding format") from exc

    if is_blocklisted(embedding_vector):
        return APIResponse(
            success=False,
            message="Upload blocked: image matches blocklisted content",
        )

    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image = Image(user_id=user.id, image_url=file_path)
    db.add(image)
    db.commit()
    db.refresh(image)

    vector_id = upsert_image_embedding(
        image_id=image.id,
        embedding=embedding_vector,
        model_used="custom-v1",
    )
    embedding_meta_data = EmbeddingMetadata(
        image_id=image.id,
        vector_id=vector_id,
        model_used="custom-v1",
    )
    db.add(embedding_meta_data)
    db.commit()
    
    return APIResponse(success=True, message="Image uploaded successfully")

@router.get("/", response_model=list[ImageFeedItem])
def get_images(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    like_counts = (
        select(ImageLike.image_id, func.count(ImageLike.id).label("like_count"))
        .group_by(ImageLike.image_id)
        .subquery()
    )
    comment_counts = (
        select(ImageComment.image_id, func.count(ImageComment.id).label("comment_count"))
        .group_by(ImageComment.image_id)
        .subquery()
    )
    liked_by_me = (
        select(ImageLike.image_id)
        .where(ImageLike.user_id == user.id)
        .subquery()
    )

    stmt = (
        select(
            Image,
            User,
            func.coalesce(like_counts.c.like_count, 0),
            func.coalesce(comment_counts.c.comment_count, 0),
            case((liked_by_me.c.image_id.isnot(None), True), else_=False).label("liked_by_me"),
        )
        .join(User, User.id == Image.user_id)
        .outerjoin(like_counts, like_counts.c.image_id == Image.id)
        .outerjoin(comment_counts, comment_counts.c.image_id == Image.id)
        .outerjoin(liked_by_me, liked_by_me.c.image_id == Image.id)
        .order_by(Image.created_at.desc())
    )
    rows = db.exec(stmt).all()

    items: list[ImageFeedItem] = []
    for image, owner, like_count, comment_count, liked in rows:
        items.append(
            ImageFeedItem(
                id=image.id,
                image_url=image.image_url,
                created_at=image.created_at,
                owner=ImageOwner(
                    id=owner.id,
                    email=owner.email,
                    username=owner.username,
                    avatar_url=owner.avatar_url,
                ),
                is_deleted=bool(image.is_deleted),
                like_count=int(like_count or 0),
                comment_count=int(comment_count or 0),
                liked_by_me=bool(liked),
            )
        )
    return items


@router.get("/me", response_model=list[ImageFeedItem])
def get_my_images(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    like_counts = (
        select(ImageLike.image_id, func.count(ImageLike.id).label("like_count"))
        .group_by(ImageLike.image_id)
        .subquery()
    )
    comment_counts = (
        select(ImageComment.image_id, func.count(ImageComment.id).label("comment_count"))
        .group_by(ImageComment.image_id)
        .subquery()
    )
    liked_by_me = (
        select(ImageLike.image_id)
        .where(ImageLike.user_id == user.id)
        .subquery()
    )

    stmt = (
        select(
            Image,
            User,
            func.coalesce(like_counts.c.like_count, 0),
            func.coalesce(comment_counts.c.comment_count, 0),
            case((liked_by_me.c.image_id.isnot(None), True), else_=False).label("liked_by_me"),
        )
        .join(User, User.id == Image.user_id)
        .outerjoin(like_counts, like_counts.c.image_id == Image.id)
        .outerjoin(comment_counts, comment_counts.c.image_id == Image.id)
        .outerjoin(liked_by_me, liked_by_me.c.image_id == Image.id)
        .where(Image.user_id == user.id)
        .order_by(Image.created_at.desc())
    )
    rows = db.exec(stmt).all()

    items: list[ImageFeedItem] = []
    for image, owner, like_count, comment_count, liked in rows:
        items.append(
            ImageFeedItem(
                id=image.id,
                image_url=image.image_url,
                created_at=image.created_at,
                owner=ImageOwner(
                    id=owner.id,
                    email=owner.email,
                    username=owner.username,
                    avatar_url=owner.avatar_url,
                ),
                is_deleted=bool(image.is_deleted),
                like_count=int(like_count or 0),
                comment_count=int(comment_count or 0),
                liked_by_me=bool(liked),
            )
        )
    return items

@router.post("/{image_id}/likes", response_model=APIResponse)
def toggle_like(
    image_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)
    if not image or image.is_deleted:
        raise HTTPException(status_code=404, detail="Image not found")

    existing = db.exec(
        select(ImageLike).where(ImageLike.image_id == image_id, ImageLike.user_id == user.id)
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        liked = False
    else:
        db.add(ImageLike(image_id=image_id, user_id=user.id))
        db.commit()
        liked = True

    like_count = db.exec(
        select(func.count(ImageLike.id)).where(ImageLike.image_id == image_id)
    ).one()

    return APIResponse(
        success=True,
        message="Like updated",
        data={"liked": liked, "like_count": int(like_count or 0)},
    )

@router.get("/{image_id}/comments", response_model=list[CommentOut])
def list_comments(
    image_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)
    if not image or image.is_deleted:
        raise HTTPException(status_code=404, detail="Image not found")

    stmt = (
        select(ImageComment, User)
        .join(User, User.id == ImageComment.user_id)
        .where(ImageComment.image_id == image_id)
        .order_by(ImageComment.created_at.asc())
    )
    rows = db.exec(stmt).all()

    items: list[CommentOut] = []
    for comment, comment_user in rows:
        items.append(
            CommentOut(
                id=comment.id,
                content=comment.content,
                created_at=comment.created_at,
                user=CommentUser(
                    id=comment_user.id,
                    username=comment_user.username,
                    avatar_url=comment_user.avatar_url,
                ),
            )
        )
    return items

@router.post("/{image_id}/comments", response_model=CommentOut)
def add_comment(
    image_id: int,
    payload: CommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)
    if not image or image.is_deleted:
        raise HTTPException(status_code=404, detail="Image not found")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    comment = ImageComment(image_id=image_id, user_id=user.id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return CommentOut(
        id=comment.id,
        content=comment.content,
        created_at=comment.created_at,
        user=CommentUser(
            id=user.id,
            username=user.username,
            avatar_url=user.avatar_url,
        ),
    )

@router.delete("/{image_id}")
def delete_image(
    image_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if image.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this image")

    image.is_deleted = True
    db.commit()

    return {"message": "Image deleted"}
