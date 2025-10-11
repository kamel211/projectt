from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt, JWTError
from database import get_db
from model.patient_model import Users
import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

# ================== إعداد التشفير و JWT ==================
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()

# ================== إعداد البريد ==================
conf = ConnectionConfig(
    MAIL_USERNAME="douh@gmail.com",
    MAIL_PASSWORD="douhash",
    MAIL_FROM="douh@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

# ================== النماذج ==================
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

class UpdatePatientRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

class TokenResponse(BaseModel):
    message: str
    access_token: str
    token_type: str

# ================== دوال JWT ==================
def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
    """
    إنشاء توكن وصول مع معلومات المستخدم
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=2)
    
    payload = {
        "sub": username,
        "id": user_id,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    """
    التحقق من صحة التوكن
    """
    if token in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ================== دوال المستخدم ==================
def register_user(db: Session, request: CreateUserRequest):
    """
    تسجيل مستخدم جديد
    """
    # التحقق من وجود المستخدم مسبقاً
    existing_user = db.query(Users).filter(
        (Users.username == request.username) | 
        (Users.email == request.email)
    ).first()
    
    if existing_user:
        if existing_user.username == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")

    # إنشاء مستخدم جديد
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
    
    return {"message": "User registered successfully", "user_id": new_user.id}

async def send_login_notification(email_to: EmailStr, username: str, ip_address: str = "غير معروف"):
    """
    إرسال إشعار تسجيل الدخول عبر البريد
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    body = f"""
مرحبًا {username}،
تم تسجيل دخول جديد إلى حسابك في النظام.

📅 التاريخ والوقت: {now}
🌐 عنوان IP: {ip_address}

إذا لم تكن أنت من قام بتسجيل الدخول، يرجى تغيير كلمة المرور فورًا.
"""
    message = MessageSchema(
        subject="تسجيل دخول جديد 👋",
        recipients=[email_to],
        body=body,
        subtype="plain"
    )
    
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        # تسجيل الخطأ دون إفشال عملية تسجيل الدخول
        print(f"Failed to send email notification: {e}")

def login_user(db: Session, request_data: LoginUserRequest, request: Request):
    """
    تسجيل دخول المستخدم
    """
    user = db.query(Users).filter(Users.username == request_data.username).first()
    
    if not user or not bcrypt_context.verify(request_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # إنشاء توكن الوصول
    token = create_access_token(user.username, user.id)
    client_host = request.client.host if request.client else "غير معروف"

    # إرسال إشعار بالبريد عند تسجيل الدخول (بدون انتظار)
    asyncio.create_task(send_login_notification(user.email, user.username, client_host))

    return {
        "message": f"Welcome {user.username}",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id
    }

def logout_user(token: str):
    """
    تسجيل خروج المستخدم
    """
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}

def change_password(request_data: ChangePasswordRequest, db: Session, current_user: Users):
    """
    تغيير كلمة المرور
    """
    if not bcrypt_context.verify(request_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")
    
    # التحقق من أن كلمة المرور الجديدة مختلفة
    if bcrypt_context.verify(request_data.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة")
    
    current_user.hashed_password = bcrypt_context.hash(request_data.new_password)
    db.commit()
    
    return {"message": "تم تغيير كلمة المرور بنجاح ✅"}

def update_patient_profile(update_data: UpdatePatientRequest, db: Session, current_user: Users):
    """
    تحديث بيانات المريض
    """
    # تحديث الحقول إذا تم تقديمها
    if update_data.first_name is not None:
        current_user.first_name = update_data.first_name
    if update_data.last_name is not None:
        current_user.last_name = update_data.last_name
    if update_data.phone_number is not None:
        current_user.phone_number = update_data.phone_number
    if update_data.email is not None:
        # التحقق من أن البريد الإلكتروني غير مستخدم من قبل مستخدم آخر
        existing_user = db.query(Users).filter(Users.email == update_data.email, Users.id != current_user.id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        current_user.email = update_data.email
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "تم تحديث البيانات بنجاح ✅",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone_number": current_user.phone_number
        }
    }

# ================== المستخدم الحالي ==================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/patients/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    الحصول على المستخدم الحالي من التوكن
    """
    username = verify_token(token)
    user = db.query(Users).filter(Users.username == username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def get_current_patient(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    اسم بديل للدالة السابقة للحفاظ على التوافقية
    """
    return get_current_user(token, db)