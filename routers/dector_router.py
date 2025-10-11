from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from database import get_db
from Controller import doctor_controller

router = APIRouter(prefix="/doctors", tags=["Doctors Auth"])

# تسجيل دكتور جديد
@router.post("/register")
def register(request: doctor_controller.CreateDoctorRequest, db: Session = Depends(get_db)):
    return doctor_controller.registerDoctor(db, request)

# تسجيل دخول دكتور
@router.post("/login")
def login(request: doctor_controller.LoginDoctorRequest, db: Session = Depends(get_db)):
    return doctor_controller.loginDoctor(db, request)

# تسجيل خروج دكتور
@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]
    return doctor_controller.logoutDoctor(token)
