from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt
from database import get_db
from model.patient_model import Users
import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()

# إعدادات البريد
conf = ConnectionConfig(
    MAIL_USERNAME="your_email@gmail.com",
    MAIL_PASSWORD="your_app_password",
    MAIL_FROM="your_email@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True
)

# ------------------ النماذج ------------------
class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class LoginUserRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# ------------------ دوال JWT ------------------
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
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------------ دوال المريض ------------------
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

async def send_login_notification(email_to: EmailStr, username: str, ip_address: str = "غير معروف"):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = "تسجيل دخول جديد إلى حسابك 👋"
    body = f"""
مرحبًا {username}،
تم تسجيل دخول جديد إلى حسابك في العيادة

📅 التاريخ والوقت: {now}
🌐 عنوان IP: {ip_address}

إذا لم تكن أنت من قام بتسجيل الدخول، يرجى تغيير كلمة المرور فورًا.

مع تحيات فريق الدعم 💙
"""
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

def loginUser(db: Session, request_data: LoginUserRequest, request: Request):
    user = db.query(Users).filter(Users.username == request_data.username).first()
    if not user or not bcrypt_context.verify(request_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user.username)
    client_host = request.client.host if request.client else "غير معروف"
    try:
        asyncio.create_task(send_login_notification(user.email, user.username, client_host))
    except Exception as e:
        print(f"فشل إرسال الإيميل: {e}")
    return {
        "message": f"Welcome {user.username}",
        "access_token": token,
        "token_type": "bearer"
    }

def logoutUser(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}

def changePassword(request_data: ChangePasswordRequest, db: Session, user: Users):
    if not bcrypt_context.verify(request_data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")
    user.hashed_password = bcrypt_context.hash(request_data.new_password)
    db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح ✅"}

# ------------------ دالة المستخدم الحالي ------------------
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_patient(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = verify_token(token)
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
