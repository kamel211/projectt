from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
import cloudinary.uploader
from database import SessionLocal
from model import images_model
from Controller.patient_controller import get_current_user  # يجب أن ترجع id و username للمستخدم

router = APIRouter(prefix="/images", tags=["Images"])

# ----------- دالة جلسة قاعدة البيانات -------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------- دالة رفع الصورة لـ Cloudinary -------------
def upload_to_cloudinary(file: UploadFile, user_id: int, db: Session):
    # تحقق من نوع الملف
    if not file.filename.lower().endswith((".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="الملف يجب أن يكون JPG أو JPEG فقط")
    
    try:
        # رفع الصورة إلى Cloudinary
        result = cloudinary.uploader.upload(file.file.read(), folder="brain_clinic")
        
        # حفظ بيانات الصورة في قاعدة البيانات
        new_image = images_model.Images(
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

# ----------- Endpoint رفع ملف واحد -------------
@router.post("/upload_file/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    return upload_to_cloudinary(file, user['id'], db)

# ----------- Endpoint رفع عدة ملفات -------------
@router.post("/upload_files/")
async def upload_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    urls = []
    for file in files:
        try:
            urls.append(upload_to_cloudinary(file, user['id'], db))
        except HTTPException as e:
            urls.append({"filename": file.filename, "error": e.detail})
    return {"files": urls}

# ----------- Endpoint استرجاع كل صور المستخدم الحالي -------------
@router.get("/me")
def get_my_images(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    images = db.query(images_model.Images).filter(images_model.Images.user_id == user['id']).all()
    return images
