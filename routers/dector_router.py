import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from Controller import doctor_controller
from model.doctor_model import LoginDoctorModel, UpdateDoctorModel
from Controller.doctor_controller import get_all_doctors, get_current_doctor, get_doctor_by_id, update_doctor  
router = APIRouter(prefix="/doctors", tags=["Doctors"])


# ✅ تسجيل دكتور جديد مع رفع CV
@router.post("/register")
def register_doctor_with_cv(
    username: str = Form(...),
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(...),
    role: str = Form("doctor"),
    cv_file: UploadFile = File(...)
):
    return doctor_controller.register_doctor_with_cv(
        username, email, first_name, last_name, password, phone_number, role, cv_file
    )

# ✅ تسجيل الدخول
@router.post("/login")
def login_doctor(request: LoginDoctorModel, req: Request):
    return doctor_controller.login_doctor(request, req)


# ✅ الحصول على بياناتي
@router.get("/me")
def get_my_data(current_user=Depends(doctor_controller.get_current_doctor)):
    return current_user

# ===========================
# 📌 الحصول على جميع الدكاترة
# ===========================
@router.get("/all")
async def all_doctors():
    return {"status": True, "data": get_all_doctors()}

@router.get("/{doctor_id}")
async def doctor_by_id(doctor_id: str):
    doctor = get_doctor_by_id(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.put("/update")
async def update_profile(
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    years_of_experience: Optional[int] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_doctor)
):
    from Controller.doctor_controller import update_doctor
    import os

    update_data = UpdateDoctorModel(
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        email=email,
        bio=bio,
        location=location,
        gender=gender,
        specialization=specialization,
        years_of_experience=years_of_experience
    )

    # حفظ الصورة على السيرفر إذا تم رفعها
    if profile_image:
        ext = profile_image.filename.split(".")[-1]
        file_path = f"uploads/profile_images/{current_user['_id']}_profile.{ext}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(await profile_image.read())
        update_data.profile_image_url = file_path  # حفظ مسار الصورة

    # تحديث بيانات الدكتور
    doctor = update_doctor(update_data, current_user)

    return {
        "status": "success",
        "message": "Profile updated successfully",
        "data": doctor
    }


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # حفظ الملف
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        contents = await file.read()
        f.write(contents)
    return {"filename": file.filename, "message": "Upload successful"}