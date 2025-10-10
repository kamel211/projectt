from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt
from model.patient_model import Users
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import asyncio

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ----------- إعدادات التشفير وJWT -------------
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()

# ----------- إعدادات البريد الإلكتروني -------------
conf = ConnectionConfig(
    MAIL_USERNAME="your_email@gmail.com",
    MAIL_PASSWORD="your_app_password",  # App Password من Gmail
    MAIL_FROM="your_email@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True
)

async def send_login_notification(email_to: EmailStr, username: str, ip_address: str = "غير معروف"):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = "تسجيل دخول جديد إلى حسابك 👋"
    body = f"""
مرحبًا {username}،
تم تسجيل دخول جديد إلى حسابك في العيادة الامل

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

# ----------- النماذج -------------
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

# ----------- دوال JWT -------------
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

# تسجيل مستخدم جديد
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

# تسجيل دخول المستخدم
def loginUser(db: Session, request_data: LoginUserRequest, request: Request):
    user = db.query(Users).filter(Users.username == request_data.username).first()
    if not user or not bcrypt_context.verify(request_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user.username)

    # الحصول على IP المستخدم
    client_host = request.client.host if request.client else "غير معروف"

    # إرسال الإيميل بالخلفية
    try:
        asyncio.create_task(send_login_notification(user.email, user.username, client_host))
    except Exception as e:
        print(f"فشل إرسال الإيميل: {e}")

    return {
        "message": f"Welcome {user.username}",
        "access_token": token,
        "token_type": "bearer"
    }

# تسجيل الخروج
def logoutUser(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}
