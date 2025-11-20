# patient_controller.py
import aiosmtplib
from email.mime.text import MIMEText
import logging
import random
from database import otp_collection, patients_collection  
from Controller.otp_controller import PatientController
from fastapi import HTTPException, Depends, Request, status
from passlib.context import CryptContext
from model.otp_model import OTPRequest, OTPVerifyRequest
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from bson import ObjectId
from Controller.otp_controller import PatientController

# ================== استدعاء الاتصال من database.py ==================
from database import mongo_db

patient_controller = PatientController()

# مجموعة المرضى
patients_collection = mongo_db["patients"]

# ================== إعداد التشفير و JWT ==================
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
blacklisted_tokens = set()

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
def create_access_token(email: str, patient_id: str, expires_delta: Optional[timedelta] = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=2))
    payload = {"sub": email, "id": patient_id, "role": "patient", "exp": expire}
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
async def register_patient(request: CreatePatientRequest):
    # تحقق إذا كان المستخدم موجود مسبقًا
    existing_patient = await patients_collection.find_one({
    "$or": [{"username": request.username}, {"email": request.email}]
})


    if existing_patient:
        if existing_patient["username"] == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            raise HTTPException(status_code=400, detail="Email already exists")

    # تشفير الباسورد
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

    # إدخال المستخدم الجديد في قاعدة البيانات
    result = await patients_collection.insert_one(new_patient)
    return {"message": "Patient registered successfully", "patient_id": str(result.inserted_id)}






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


# ================= SMTP =================
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 465
SMTP_LOGIN = "9b77a8001@smtp-brevo.com"
SMTP_PASSWORD = "WSn3aDfVAKMhJwrd"
FROM_EMAIL = "عياده الامل <douhasharkawi@gmail.com>"
# ================= JWT =================
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

class PatientController:
    def __init__(self):
        self.otp_collection = otp_collection  # تم تعريفها داخل الكلاس

    async def startup_event(self):
        await self.otp_collection.create_index("expires", expireAfterSeconds=0)

        logging.info(" TTL index on otp_storage collection is ready.")

    def generate_otp(self):
        return str(random.randint(100000, 999999))

    async def store_otp(self, email: str):
        otp_code = self.generate_otp()
        doc = {
            "email": email, 
            "otp": otp_code,
            "expires": datetime.utcnow() + timedelta(minutes=5),
            "attempts": 0
        }
        result = await self.otp_collection.update_one({"email": email}, {"$set": doc}, upsert=True)

        logging.info(f"OTP for {email} stored in DB: {otp_code} | Upserted: {result.upserted_id}")
        return otp_code

    async def verify_otp(self, email: str, otp: str):
        entry = await otp_collection.find_one({"email": email})
        if not entry:
            raise HTTPException(status_code=400, detail="لم يتم العثور على كود OTP")
        
        if datetime.utcnow() > entry["expires"]:
            logging.warning(f"OTP for {email} expired at {entry['expires']}")
            await otp_collection.delete_one({"email": email})
            raise HTTPException(status_code=400, detail="انتهت صلاحية OTP")
        
        if entry["attempts"] >= 5:
            raise HTTPException(status_code=400, detail="تم تجاوز عدد المحاولات المسموح بها")
        
        if entry["otp"] != otp:
            await otp_collection.update_one({"email": email}, {"$inc": {"attempts": 1}})
            raise HTTPException(status_code=400, detail="رمز التحقق غير صحيح")
        
        await otp_collection.update_one({"email": email}, {"$set": {"verified": True}})
        logging.info(f"OTP for {email} verified successfully (kept in DB)")
        return True

    async def send_email(self, recipient, otp_code):
        message = message = MIMEText(f"""
 عيادة الأمل 
-----------------
مرحباً بك في عيادتنا

🔑 رمز التحقق: {otp_code}

شكراً لاختيارك عيادة الأمل
""", "plain", "utf-8")
        
        message["From"] = FROM_EMAIL
        message["To"] = recipient
        message["Subject"] = "رمز التحقق (OTP)"

        try:
            
            await aiosmtplib.send(
                message,
                hostname=SMTP_SERVER,
                port=SMTP_PORT,
                use_tls=True,   # بدل start_tls
                username=SMTP_LOGIN,
                password=SMTP_PASSWORD
            )

            logging.info(f"OTP sent to {recipient}")
        except Exception as e:
            logging.error(f" Error sending email to {recipient}: {e}")
            raise HTTPException(status_code=500, detail="فشل إرسال البريد الإلكتروني")

    def create_access_token(self, username: str, patient_id: str, expires_delta: timedelta = timedelta(hours=2)):
        expire = datetime.utcnow() + expires_delta
        payload = {"sub": username, "id": patient_id, "role": "patient", "exp": expire}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    async def send_otp_endpoint(self, request: OTPRequest):
        patient = await patients_collection.find_one({"email": request.email})
        if not patient:
            raise HTTPException(status_code=404, detail="البريد غير مسجل")
        
        otp_code = await self.store_otp(request.email)
        await self.send_email(request.email, otp_code)
        return {"message": "تم إرسال رمز التحقق إلى البريد الإلكتروني"}

    async def verify_login_otp(self, request: OTPVerifyRequest):
        patient = await patients_collection.find_one({"email": request.email})
        if not patient:
            raise HTTPException(status_code=404, detail="البريد غير مسجل")
        
        await self.verify_otp(request.email, request.otp)
        token = self.create_access_token(patient["username"], str(patient["_id"]))
        return {
            "message": f"مرحباً {patient['first_name']}!",
            "access_token": token,
            "token_type": "bearer",
            "patient_id": str(patient["_id"])
        }

# إنشاء instance من ال controller
patient_controller = PatientController()