from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import cloudinary.uploader
from Controller.patient_controller import get_current_patient
from model.images_model import Images

router = APIRouter(prefix="/images", tags=["Images"])

def upload_to_cloudinary(file: UploadFile, user_id: int, db: Session):
    if not file.filename.lower().endswith((".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="الملف يجب أن يكون JPG أو JPEG فقط")
    try:
        result = cloudinary.uploader.upload(file.file.read(), folder="brain_clinic")
        new_image = Images(
            filename=file.filename,
            url=result["secure_url"],
            user_id=user_id
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        return {"id": new_image.id, "filename": new_image.filename, "url": new_image.url, "user_id": new_image.user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل الرفع: {str(e)}")

# رفع ملف واحد
@router.post("/upload_file/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), user = Depends(get_current_patient)):
    return upload_to_cloudinary(file, user.id, db)

# رفع عدة ملفات
@router.post("/upload_files/")
async def upload_files(files: list[UploadFile] = File(...), db: Session = Depends(get_db), user = Depends(get_current_patient)):
    urls = []
    for file in files:
        try:
            urls.append(upload_to_cloudinary(file, user.id, db))
        except HTTPException as e:
            urls.append({"filename": file.filename, "error": e.detail})
    return {"files": urls}

# استرجاع كل صور المستخدم
@router.get("/me")
def get_my_images(db: Session = Depends(get_db), user = Depends(get_current_patient)):
    images = db.query(Images).filter(Images.user_id == user.id).all()
    return images
