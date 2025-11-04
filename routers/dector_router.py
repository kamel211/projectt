from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from Controller import doctor_controller
from model.doctor_model import LoginDoctorModel, UpdateDoctorModel

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

# ✅ تحديث الملف الشخصي
@router.put("/update")
def update_profile(update_data: UpdateDoctorModel, current_user=Depends(doctor_controller.get_current_doctor)):
    return doctor_controller.update_doctor(update_data, current_user)

# ✅ الحصول على بياناتي
@router.get("/me")
def get_my_data(current_user=Depends(doctor_controller.get_current_doctor)):
    return current_user
