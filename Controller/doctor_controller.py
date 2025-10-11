from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
from model.doctor_model import Doctors

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()

class CreateDoctorRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class LoginDoctorRequest(BaseModel):
    username: str
    password: str

def create_access_token(username: str):
    expire = datetime.utcnow() + timedelta(hours=2)
    payload = {"sub": username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str):
    if token in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def registerDoctor(db: Session, request: CreateDoctorRequest):
    existing = db.query(Doctors).filter(Doctors.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_doctor = Doctors(
        email=request.email,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        hashed_password=bcrypt_context.hash(request.password),
        phone_number=request.phone_number
    )
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return {"message": "Doctor registered successfully"}

def loginDoctor(db: Session, request: LoginDoctorRequest):
    doctor = db.query(Doctors).filter(Doctors.username == request.username).first()
    if not doctor or not bcrypt_context.verify(request.password, doctor.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(doctor.username)
    return {"message": f"Welcome Dr. {doctor.username}", "access_token": token, "token_type": "bearer"}

def logoutDoctor(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}
