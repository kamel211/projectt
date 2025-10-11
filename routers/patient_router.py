from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from database import get_db
from Controller import patient_controller
from Controller.patient_controller import ChangePasswordRequest, changePassword, get_current_patient
from model.patient_model import Users

router = APIRouter(prefix="/users", tags=["Users Auth"])

# تسجيل مستخدم جديد
@router.post("/register")
def register(request: patient_controller.CreateUserRequest, db: Session = Depends(get_db)):
    return patient_controller.registerUser(db, request)

# تسجيل الدخول
@router.post("/login")
def login(request: patient_controller.LoginUserRequest, db: Session = Depends(get_db), req: Request = None):
    return patient_controller.loginUser(db, request, req)

# تسجيل الخروج
@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]
    return patient_controller.logoutUser(token)

# تغيير كلمة المرور
@router.put("/change-password")
def change_password(
    request_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    return changePassword(request_data, db, user)
