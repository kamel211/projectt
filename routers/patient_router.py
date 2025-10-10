from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from database import get_db
from Controller import patient_controller

router = APIRouter(prefix="/users", tags=["Users Auth"])

@router.post("/register")
def register(request:patient_controller.CreateUserRequest, db: Session = Depends(get_db)):
    return patient_controller.registerUser(db, request)

@router.post("/login")
def login(request: patient_controller.LoginUserRequest, db: Session = Depends(get_db)):
    return patient_controller.loginUser(db, request)

@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]  # نأخذ التوكن من الهيدر
    return patient_controller.logoutUser(token)
