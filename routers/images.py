from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
import cloudinary.uploader
from database import SessionLocal
import models
from routers.auth import get_current_user  # نجيب الدالة من auth

router = APIRouter(
    prefix="/images",
    tags=["Images"]
)

# تابع لجلسة قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Depends(get_db)
user_dependency = Depends(get_current_user)  # المستخدم الحالي من التوكن

# دالة داخلية لإعادة استخدام الكود
def upload_to_cloudinary(file: UploadFile, user_id: int, db: Session):
    if not file.filename.lower().endswith((".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="الملف يجب أن يكون JPG فقط")
    try:
        result = cloudinary.uploader.upload(file.file.read(), folder="brain_clinic")
        new_image = models.Images(
            filename=file.filename,
            url=result["secure_url"],
            user_id=user_id
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        return {
            "id": new_image.id,
            "filename": new_image.filename,
            "url": new_image.url,
            "user_id": new_image.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل الرفع: {str(e)}")

# رفع ملف واحد
@router.post("/upload_file/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = db_dependency,
    user: dict = user_dependency
):
    return upload_to_cloudinary(file, user['id'], db)

# رفع عدة ملفات
@router.post("/upload_files/")
async def upload_files(
    files: List[UploadFile] = File(...),
    db: Session = db_dependency,
    user: dict = user_dependency
):
    urls = []
    for file in files:
        try:
            urls.append(upload_to_cloudinary(file, user['id'], db))
        except HTTPException as e:
            urls.append({"filename": file.filename, "error": e.detail})
    return {"files": urls}

# استرجاع كل صور المستخدم الحالي
@router.get("/me")
def get_my_images(
    db: Session = db_dependency,
    user: dict = user_dependency
):
    images = db.query(models.Images).filter(models.Images.user_id == user['id']).all()
    return images
