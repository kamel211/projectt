from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from database import get_db
from Controller.patient_controller import (
    CreateUserRequest, 
    LoginUserRequest, 
    ChangePasswordRequest, 
    UpdatePatientRequest,
    register_user, 
    login_user, 
    logout_user, 
    change_password,
    update_patient_profile,
    get_current_patient
)
from model.patient_model import Users

router = APIRouter(prefix="/patients", tags=["Patients Auth"])

# ---------------- تسجيل مريض جديد ----------------
@router.post("/register")
def register(request: CreateUserRequest, db: Session = Depends(get_db)):
    return register_user(db, request)

# ---------------- تسجيل الدخول ----------------
@router.post("/login")
def login(request: LoginUserRequest, db: Session = Depends(get_db), req: Request = None):
    return login_user(db, request, req)

# ---------------- تسجيل الخروج ----------------
@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]
    return logout_user(token)

# ---------------- تغيير كلمة المرور ----------------
@router.put("/change-password")
def change_patient_password(
    request_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    return change_password(request_data, db, user)

# ---------------- عرض بيانات المريض الحالي ----------------
@router.get("/me")
def get_current_patient_info(user: Users = Depends(get_current_patient)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "full_name": f"{user.first_name} {user.last_name}"
    }

# ---------------- تحديث بيانات المريض ----------------
@router.put("/profile")
def update_patient_profile_endpoint(
    update_data: UpdatePatientRequest,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    return update_patient_profile(update_data, db, user)
