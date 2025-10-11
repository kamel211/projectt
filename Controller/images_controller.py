from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import cloudinary.uploader
from model import images_model
from typing import List
import io

# ----------- إعداد أنواع الملفات المدعومة -------------
ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png")  # JPG و JPEG و PNG

# ----------- رفع صورة واحدة إلى Cloudinary وحفظها -------------
def upload_single_image(file: UploadFile, user_id: int, db: Session):
    filename = file.filename.lower()
    if not filename.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail=f"الملف يجب أن يكون أحد الأنواع: {', '.join(ALLOWED_EXTENSIONS)}")
    
    try:
        # قراءة محتوى الملف في بايتس
        file_content = file.file.read()
        file.file.close()  # إغلاق الملف بعد القراءة
        
        # رفع الصورة إلى Cloudinary
        result = cloudinary.uploader.upload(io.BytesIO(file_content), folder="brain_clinic")
        
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
        raise HTTPException(status_code=500, detail=f"فشل رفع الصورة: {str(e)}")


# ----------- رفع عدة صور دفعة واحدة -------------
def upload_multiple_images(files: List[UploadFile], user_id: int, db: Session):
    results = []
    for file in files:
        try:
            results.append(upload_single_image(file, user_id, db))
        except HTTPException as e:
            results.append({"filename": file.filename, "error": e.detail})
    return results


# ----------- استرجاع صور المستخدم -------------
def get_user_images(db: Session, user_id: int):
    return db.query(images_model.Images).filter(images_model.Images.user_id == user_id).all()
