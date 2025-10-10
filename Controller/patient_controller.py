from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from model.patient_model import Users

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()

# ----------- النماذج -------------
class CreateUserRequest(BaseModel):
    username:str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class LoginUserRequest(BaseModel):
    username: str
    password: str

# ----------- دوال مساعدة -------------
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
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ----------- الوظائف الرئيسية -------------
def registerUser(db: Session, request: CreateUserRequest):
    existing_user = db.query(Users).filter(Users.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = Users(
        email=request.email,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        hashed_password=bcrypt_context.hash(request.password),
        phone_number=request.phone_number
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

def loginUser(db: Session, request: LoginUserRequest):
    user = db.query(Users).filter(Users.username == request.username).first()
    if not user or not bcrypt_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.username)
    return {
        "message": f"Welcome {user.username}",
        "access_token": token,
        "token_type": "bearer"
    }

def logoutUser(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}
