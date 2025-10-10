from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from database import get_db
from Controller import doctor_controller

router = APIRouter(prefix="/dector", tags=["Dector Auth"])

@router.post("/register")
def register(request: doctor_controller.CreateDectorRequest, db: Session = Depends(get_db)):
    return doctor_controller.registerDector(db, request)

@router.post("/login")
def login(request: doctor_controller.LoginDectorRequest, db: Session = Depends(get_db)):
    return doctor_controller.loginDector(db, request)

@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]  # نأخذ التوكن من الهيدر
    return doctor_controller.logoutDector(token)