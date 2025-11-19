# patient_controller.py
from fastapi import HTTPException, Depends, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from bson import ObjectId

# ================== استدعاء الاتصال من database.py ==================
from database import mongo_db

# مجموعة المرضى
patients_collection = mongo_db["patients"]

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
class CreatePatientRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    phone_number: str

class LoginPatientRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UpdatePatientRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

class TokenResponse(BaseModel):
    message: str
    access_token: str
    token_type: str

# ======= truncate password to 72 bytes =======
def truncate_password(password: str) -> str:
    """
    تقص الباسورد إلى أول 72 بايت بشكل آمن لباسوردات UTF-8.
    """
    # loop عبر الأحرف وحساب الطول بالبايت
    truncated = ""
    total_bytes = 0
    for char in password:
        char_bytes = char.encode("utf-8")
        if total_bytes + len(char_bytes) > 72:
            break
        truncated += char
        total_bytes += len(char_bytes)
    return truncated

# ================== دوال JWT ==================
def create_access_token(username: str, patient_id: str, expires_delta: Optional[timedelta] = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=2))
    payload = {"sub": username, "id": patient_id, "role": "patient", "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    if token in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or role != "patient":
            raise HTTPException(status_code=401, detail="Invalid token or role")
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ================== تسجيل مريض جديد ==================
def register_patient(request: CreatePatientRequest):
# لم يعد هناك حاجة للتحقق من طول الباسورد

    existing_patient = patients_collection.find_one({
        "$or": [{"username": request.username}, {"email": request.email}]
    })
    if existing_patient:
        if existing_patient["username"] == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = bcrypt_context.hash(truncate_password(request.password))
    new_patient = {
        "email": request.email,
        "username": request.username,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "role": "patient",
        "hashed_password": hashed_password,
        "phone_number": request.phone_number,
        "appointments": [],
        "is_active": True,
        "created_at": datetime.utcnow()
    }

    result = patients_collection.insert_one(new_patient)
    return {"message": "Patient registered successfully", "patient_id": str(result.inserted_id)}


# ================== تسجيل الدخول ==================
from fastapi import HTTPException, Request
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def login_patient(request_data: LoginPatientRequest, request: Request):
    """
    Login a patient using username or email and password.
    Returns an access token and patient info if successful.
    """

    # 1️⃣ Build the query based on provided input
    query = {}
    if request_data.username:
        query["username"] = request_data.username
    elif request_data.email:
        query["email"] = request_data.email
    else:
        # Case: Neither username nor email is provided
        raise HTTPException(
            status_code=400,
            detail="Please provide either username or email."
        )

    # 2️⃣ Find patient in the database
    patient = patients_collection.find_one(query)

    # 3️⃣ Check if patient exists and password is correct
    if not patient:
        # Case: No patient found with the given username/email
        raise HTTPException(
            status_code=401,
            detail="Username or password is incorrect."
        )

    if not bcrypt_context.verify(request_data.password, patient["hashed_password"]):
        # Case: Password is incorrect
        raise HTTPException(
            status_code=401,
            detail="Username or password is incorrect."
        )

    # 4️⃣ Check if account is active
    if not patient.get("is_active", True):
        # Case: Account exists but is inactive
        raise HTTPException(
            status_code=403,
            detail="Account is inactive. Please contact administration."
        )

    # 5️⃣ If everything is fine, create an access token
    token = create_access_token(patient["username"], str(patient["_id"]))

    # 6️⃣ Return success response
    return {
        "message": f"Welcome back, {patient['first_name']}!",
        "access_token": token,
        "token_type": "bearer",
        "patient_id": str(patient["_id"]),
        "patient_data": {
            "username": patient["username"],
            "email": patient["email"],
            "full_name": f"{patient['first_name']} {patient['last_name']}",
            "role": "patient"
        }
    }


# ================== المريض الحالي ==================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/patients/login")


def get_current_patient(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token: no email found")
        
        patient = patients_collection.find_one({"email": email})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # تحويل ObjectId إلى string
        patient["_id"] = str(patient["_id"])
        return patient

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ================== تسجيل الخروج ==================
def logout_patient(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}


# ================== تغيير كلمة المرور ==================
def change_password(request_data: ChangePasswordRequest, current_patient):
    if not bcrypt_context.verify(request_data.old_password, current_patient["hashed_password"]):
        raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")

    if bcrypt_context.verify(request_data.new_password, current_patient["hashed_password"]):
        raise HTTPException(status_code=400, detail="كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة")

    hashed_new_password = bcrypt_context.hash(truncate_password(request_data.new_password))
    patients_collection.update_one(
        {"_id": ObjectId(current_patient["_id"])},
        {"$set": {"hashed_password": hashed_new_password}}
    )

    return {"message": "تم تغيير كلمة المرور بنجاح ✅"}


# ================== تحديث الملف الشخصي ==================
def update_patient_profile(update_data: UpdatePatientRequest, current_patient):
    updates = {}

    if update_data.first_name:
        updates["first_name"] = update_data.first_name
    if update_data.last_name:
        updates["last_name"] = update_data.last_name
    if update_data.phone_number:
        existing_phone = patients_collection.find_one({
            "phone_number": update_data.phone_number,
            "_id": {"$ne": ObjectId(current_patient["_id"])}
        })
        if existing_phone:
            raise HTTPException(status_code=400, detail="رقم الهاتف مستخدم من قبل ❌")
        updates["phone_number"] = update_data.phone_number
    if update_data.email:
        existing_email = patients_collection.find_one({
            "email": update_data.email,
            "_id": {"$ne": ObjectId(current_patient["_id"])}
        })
        if existing_email:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم مسبقًا ❌")
        updates["email"] = update_data.email
    if update_data.username:
        existing_patient = patients_collection.find_one({
            "username": update_data.username,
            "_id": {"$ne": ObjectId(current_patient["_id"])}
        })
        if existing_patient:
            raise HTTPException(status_code=409, detail="اسم المستخدم مستخدم مسبقًا ❌")
        updates["username"] = update_data.username

    if updates:
        patients_collection.update_one({"_id": ObjectId(current_patient["_id"])}, {"$set": updates})

    updated_patient = patients_collection.find_one({"_id": ObjectId(current_patient["_id"])})
    updated_patient["_id"] = str(updated_patient["_id"])

    profile_data = {
        "full_name": f"{updated_patient['first_name']} {updated_patient['last_name']}".strip(),
        "username": updated_patient["username"],
        "email": updated_patient["email"],
        "phone_number": updated_patient.get("phone_number", "")
    }

    return {"message": "تم تحديث البيانات بنجاح ✅", "patient": profile_data}


# ================== عرض الملف الشخصي ==================
def get_profile_for_current_patient(current_patient: dict):
    return {
        "full_name": f"{current_patient.get('first_name', '')} {current_patient.get('last_name', '')}".strip(),
        "email": current_patient.get("email"),
        "phone_number": current_patient.get("phone_number"),
        "username": current_patient.get("username"),
    }







# ================== استدعاء مجموعة الدكاترة ==================
doctors_collection = mongo_db["doctors"]

# ================== جلب كل معلومات دكتور ==================
def get_doctor_info(doctor_id: str):
    """
    ترجع كل بيانات الدكتور بناءً على الID.
    """

    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # تحويل ObjectId إلى string
    doctor["_id"] = str(doctor["_id"])

    # إرجاع كل البيانات للمريض
    return doctor

# ================== جلب كل الدكاترة ==================
def get_all_doctors_info():
    """
    ترجع قائمة بكل الدكاترة.
    """
    doctors_cursor = doctors_collection.find()
    doctors_list = []
    for doc in doctors_cursor:
        doc["_id"] = str(doc["_id"])
        doctors_list.append(doc)
    return doctors_list


##
##
##
##
##
##
##
##
##
##
##
##
'''from fastapi import HTTPException, Depends, Request
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
    existing_user = db.query(Users).filter(
        (Users.username == request.username) | 
        (Users.email == request.email)
    ).first()
    
    if existing_user:
        if existing_user.username == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")

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

async def send_login_notification(email_to: EmailStr, user: Users, ip_address: str = "غير معروف"):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    body = f"""
مرحبًا {user.get_full_name()}،
تم تسجيل دخول جديد إلى حسابك في النظام.

📅 التاريخ والوقت: {now}
🌐 عنوان IP: {ip_address}
👤 اسم المستخدم: {user.username}

إذا لم تكن أنت من قام بتسجيل الدخول، يرجى تغيير كلمة المرور فورًا."
 

    message = MessageSchema(
        subject="تسجيل دخول جديد 👋 - نظام إدارة المستشفى",
        recipients=[email_to],
        body=body,
        subtype="plain"
    )"""
    
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"✅ تم إرسال إشعار التسجيل إلى {email_to}")
    except Exception as e:
        print(f"❌ فشل إرسال الإشعار إلى {email_to}: {e}")

def login_user(db: Session, request_data: LoginUserRequest, request: Request):
    user = db.query(Users).filter(Users.username == request_data.username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not bcrypt_context.verify(request_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="الحساب غير مفعل. يرجى التواصل مع الإدارة.")

    token = create_access_token(user.username, user.id)
    client_host = request.client.host if request.client else "غير معروف"

    asyncio.create_task(send_login_notification(user.email, user, client_host))

    return {
        "message": f"مرحباً بعودتك {user.get_full_name()}!",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_data": {
            "username": user.username,
            "email": user.email,
            "full_name": user.get_full_name(),
            "role": user.role
        }
    }

def logout_user(token: str):
    blacklisted_tokens.add(token)
    return {"message": "Logged out successfully"}

def change_password(request_data: ChangePasswordRequest, db: Session, current_user: Users):
    if not bcrypt_context.verify(request_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")
    
    if bcrypt_context.verify(request_data.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة")
    
    current_user.hashed_password = bcrypt_context.hash(request_data.new_password)
    db.commit()
    
    return {"message": "تم تغيير كلمة المرور بنجاح ✅"}

def update_patient_profile(update_data: UpdatePatientRequest, db: Session, current_user: Users):
    if update_data.first_name is not None:
        current_user.first_name = update_data.first_name
    if update_data.last_name is not None:
        current_user.last_name = update_data.last_name
    if update_data.phone_number is not None:
        current_user.phone_number = update_data.phone_number
    if update_data.email is not None:
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
    username = verify_token(token)
    user = db.query(Users).filter(Users.username == username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def get_current_patient(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return get_current_user(token, db)'''








##########
##########
##########
##########
##########
##########
##########
##########
##########
##########
##########
##########
##########
##########
##########
##########
##########














# from fastapi import HTTPException, Depends, Request
# from sqlalchemy.orm import Session
# from passlib.context import CryptContext
# from pydantic import BaseModel, EmailStr
# from datetime import datetime, timedelta
# from jose import jwt, JWTError
# from database import get_db
# from model.patient_model import Users
# import asyncio
# from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
# from fastapi.security import OAuth2PasswordBearer
# from typing import Optional

# # ================== إعداد التشفير و JWT ==================
# bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# SECRET_KEY = "mysecretkey"
# ALGORITHM = "HS256"
# blacklisted_tokens = set()

# # ================== إعداد البريد ==================
# conf = ConnectionConfig(
#     MAIL_USERNAME="douh@gmail.com",
#     MAIL_PASSWORD="douhash",
#     MAIL_FROM="douh@gmail.com",
#     MAIL_PORT=587,
#     MAIL_SERVER="smtp.gmail.com",
#     MAIL_STARTTLS=True,
#     MAIL_SSL_TLS=False,
#     USE_CREDENTIALS=True
# )

# # ================== النماذج ==================
# class CreateUserRequest(BaseModel):
#     username: str
#     email: EmailStr
#     first_name: str
#     last_name: str
#     password: str
#     role: str
#     phone_number: str

# class LoginUserRequest(BaseModel):
#     username: str
#     password: str

# class ChangePasswordRequest(BaseModel):
#     old_password: str
#     new_password: str

# class UpdatePatientRequest(BaseModel):
#     first_name: Optional[str] = None
#     last_name: Optional[str] = None
#     phone_number: Optional[str] = None
#     email: Optional[EmailStr] = None

# class TokenResponse(BaseModel):
#     message: str
#     access_token: str
#     token_type: str

# # ================== دوال JWT ==================
# def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(hours=2)
    
#     payload = {
#         "sub": username,
#         "id": user_id,
#         "exp": expire
#     }
#     return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# def verify_token(token: str):
#     if token in blacklisted_tokens:
#         raise HTTPException(status_code=401, detail="Session expired. Please login again.")
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
#         return username
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")

# # ================== دوال المستخدم ==================
# def register_user(db: Session, request: CreateUserRequest):
#     existing_user = db.query(Users).filter(
#         (Users.username == request.username) | 
#         (Users.email == request.email)
#     ).first()
    
#     if existing_user:
#         if existing_user.username == request.username:
#             raise HTTPException(status_code=400, detail="Username already exists")
#         else:
#             raise HTTPException(status_code=400, detail="Email already exists")

#     new_user = Users(
#         email=request.email,
#         username=request.username,
#         first_name=request.first_name,
#         last_name=request.last_name,
#         role=request.role,
#         hashed_password=bcrypt_context.hash(request.password),
#         phone_number=request.phone_number
#     )
    
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
    
#     return {"message": "User registered successfully", "user_id": new_user.id}

# async def send_login_notification(email_to: EmailStr, user: Users, ip_address: str = "غير معروف"):
#     now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
#     body = f"""
# مرحبًا {user.get_full_name()}،
# تم تسجيل دخول جديد إلى حسابك في النظام.

# 📅 التاريخ والوقت: {now}
# 🌐 عنوان IP: {ip_address}
# 👤 اسم المستخدم: {user.username}

# إذا لم تكن أنت من قام بتسجيل الدخول، يرجى تغيير كلمة المرور فورًا."""

#     message = MessageSchema(
#         subject="تسجيل دخول جديد 👋 - نظام إدارة المستشفى",
#         recipients=[email_to],
#         body=body,
#         subtype="plain"
#     )
    
#     try:
#         fm = FastMail(conf)
#         await fm.send_message(message)
#         print(f"✅ تم إرسال إشعار التسجيل إلى {email_to}")
#     except Exception as e:
#         print(f"❌ فشل إرسال الإشعار إلى {email_to}: {e}")

# def login_user(db: Session, request_data: LoginUserRequest, request: Request):
#     user = db.query(Users).filter(Users.username == request_data.username).first()
    
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid username or password")
    
#     if not bcrypt_context.verify(request_data.password, user.hashed_password):
#         raise HTTPException(status_code=401, detail="Invalid username or password")

#     if not user.is_active:
#         raise HTTPException(status_code=400, detail="الحساب غير مفعل. يرجى التواصل مع الإدارة.")

#     token = create_access_token(user.username, user.id)
#     client_host = request.client.host if request.client else "غير معروف"

#     asyncio.create_task(send_login_notification(user.email, user, client_host))

#     return {
#         "message": f"مرحباً بعودتك {user.get_full_name()}!",
#         "access_token": token,
#         "token_type": "bearer",
#         "user_id": user.id,
#         "user_data": {
#             "username": user.username,
#             "email": user.email,
#             "full_name": user.get_full_name(),
#             "role": user.role
#         }
#     }

# def logout_user(token: str):
#     blacklisted_tokens.add(token)
#     return {"message": "Logged out successfully"}

# def change_password(request_data: ChangePasswordRequest, db: Session, current_user: Users):
#     if not bcrypt_context.verify(request_data.old_password, current_user.hashed_password):
#         raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")
    
#     if bcrypt_context.verify(request_data.new_password, current_user.hashed_password):
#         raise HTTPException(status_code=400, detail="كلمة المرور الجديدة يجب أن تكون مختلفة عن القديمة")
    
#     current_user.hashed_password = bcrypt_context.hash(request_data.new_password)
#     db.commit()
    
#     return {"message": "تم تغيير كلمة المرور بنجاح ✅"}

# def update_patient_profile(update_data: UpdatePatientRequest, db: Session, current_user: Users):
#     if update_data.first_name is not None:
#         current_user.first_name = update_data.first_name
#     if update_data.last_name is not None:
#         current_user.last_name = update_data.last_name
#     if update_data.phone_number is not None:
#         current_user.phone_number = update_data.phone_number
#     if update_data.email is not None:
#         existing_user = db.query(Users).filter(Users.email == update_data.email, Users.id != current_user.id).first()
#         if existing_user:
#             raise HTTPException(status_code=400, detail="Email already exists")
#         current_user.email = update_data.email
    
#     db.commit()
#     db.refresh(current_user)
    
#     return {
#         "message": "تم تحديث البيانات بنجاح ✅",
#         "user": {
#             "id": current_user.id,
#             "username": current_user.username,
#             "email": current_user.email,
#             "first_name": current_user.first_name,
#             "last_name": current_user.last_name,
#             "phone_number": current_user.phone_number
#         }
#     }

# # ================== المستخدم الحالي ==================
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/patients/login")

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     username = verify_token(token)
#     user = patients_collection.find_one({"username": request_data.username});    
    
#     if not user:
#         raise HTTPException(status_code=401, detail="User not found")
    
#     return user

# def get_current_patient(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     return get_current_user(token, db)