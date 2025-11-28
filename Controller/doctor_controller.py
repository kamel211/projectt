from fastapi import HTTPException, Depends, Request, UploadFile, File
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from typing import Optional
import os
from bson import ObjectId
import os
from database import mongo_db
from model.doctor_model import UpdateDoctorModel

from database import mongo_db
from model.doctor_model import CreateDoctorModel, LoginDoctorModel, UpdateDoctorModel

# ============= الإعدادات العامة =============
doctors_collection = mongo_db["doctors"]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/doctors/login")
blacklisted_tokens = set()

# 📂 مجلد حفظ ملفات السيرة الذاتية
UPLOAD_DIR = "uploads/cv_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============= إنشاء توكن JWT =============
def create_access_token(username: str, user_id: str, role: str, expires_delta: timedelta = timedelta(hours=4)):
    payload = {"sub": username, "id": user_id, "role": role, "exp": datetime.utcnow() + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ============= تسجيل دكتور جديد مع رفع CV =============
def register_doctor_with_cv(
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    phone_number: str,
    role: str,
    cv_file: UploadFile = File(...)
):
    # 📌 التحقق من نوع الملف
    allowed_types = [
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp"
    ]
# 📌 السماح بأي صورة أو PDF
    if not (cv_file.content_type.startswith("image/") or cv_file.content_type in ["application/pdf", "application/x-pdf", "application/octet-stream"]):
        raise HTTPException(
        status_code=400,
        detail="صيغة الملف غير مدعومة. استخدم PDF أو أي صورة."
    )


    # 📌 التحقق من وجود الحساب مسبقًا
    existing = doctors_collection.find_one({
        "$or": [{"email": email}, {"username": username}]
    })
    if existing:
        raise HTTPException(status_code=400, detail="اسم المستخدم أو البريد مستخدم بالفعل")

    # 📂 حفظ الملف محليًا
    ext = cv_file.filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{username}_cv.{ext}")
    with open(file_path, "wb") as f:
        f.write(cv_file.file.read())

    # 🔐 تشفير كلمة المرور
    hashed_password = bcrypt_context.hash(password)

    # 🧾 إنشاء سجل الدكتور
    new_doctor = {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number,
        "role": role,
        "hashed_password": hashed_password,
        "cv_url": f"/{file_path}",
        "is_approved": False,   # ✳️ ينتظر موافقة الأدمن
        "is_active": True,
        "created_at": datetime.utcnow()
    }

    doctors_collection.insert_one(new_doctor)
    return {"message": "تم إرسال طلب التسجيل بنجاح ✅ بانتظار موافقة الإدارة", "cv_url": f"/{file_path}"}


# ============= تسجيل الدخول =============

async def login_doctor(request_data: LoginDoctorModel, request: Request):
    # 1️⃣ Check if doctor exists by username or email
    doctor =await  doctors_collection.find_one({
        "$or": [{"username": request_data.username}, {"email": request_data.email}]
    })

    if not doctor:
        # Doctor not found
        raise HTTPException(
            status_code=404,
            detail="Doctor not found / Username or email does not exist"
        )

    # 2️⃣ Verify password
    if not bcrypt_context.verify(request_data.password, doctor["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password / Password is invalid"
        )

    # 3️⃣ Check if account is approved
    if not doctor.get("is_approved", False):
        raise HTTPException(
            status_code=403,
            detail="Your account is not approved yet. Please wait for admin approval."
        )

    # 4️⃣ Check if account is active (optional, e.g., banned or deactivated)
    if doctor.get("is_active", True) is False:
        raise HTTPException(
            status_code=403,
            detail="Your account is deactivated or banned. Please contact support."
        )

    # 5️⃣ Generate JWT access token
    token = create_access_token(
        username=doctor["username"],
        user_id=str(doctor["_id"]),
        role=doctor["role"]
    )

    # 6️⃣ Return response
    return {
        "message": f"Welcome Doctor {doctor['first_name']} 👋",
        "access_token": token,
        "doctor_id": str(doctor["_id"]),
        "doctor_data": {
            "full_name": f"{doctor['first_name']} {doctor['last_name']}",
            "email": doctor["email"],
            "role": doctor["role"],
            "cv_url": doctor.get("cv_url")
        }
    }
# ============= تحديث الملف الشخصي =============
# def update_doctor(update_data: UpdateDoctorModel, current_user):
#     updates = {k: v for k, v in update_data.dict().items() if v is not None}
#     if not updates:
#         raise HTTPException(status_code=400, detail="لا يوجد بيانات لتحديثها")

#     doctors_collection.update_one({"_id": ObjectId(current_user["_id"])}, {"$set": updates})
#     return {"message": "تم تحديث البيانات بنجاح ✅"}


# ============= الحصول على بيانات المستخدم الحالي =============
async def get_current_doctor(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        doctor = await doctors_collection.find_one({"_id": ObjectId(payload["id"])})
        if not doctor:
            raise HTTPException(status_code=404, detail="لم يتم العثور على الدكتور")
        doctor["_id"] = str(doctor["_id"])
        return doctor
    except JWTError:
        raise HTTPException(status_code=401, detail="رمز الدخول غير صالح")


# ============= التحقق من التوكن (تُستخدم في الشات) =============
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        doctor = doctors_collection.find_one({"_id": ObjectId(payload["id"])})
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return {"id": str(doctor["_id"]), "role": doctor["role"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")





        

def get_all_doctors():
    doctors = mongo_db["doctors"].find()
    result = []

    for d in doctors:
        result.append({
            "id": str(d["_id"]),
            "first_name": d.get("first_name"),
            "last_name": d.get("last_name"),
            "email": d.get("email"),
            "phone_number": d.get("phone_number"),
            "cv_url": d.get("cv_url"),
            "is_approved": d.get("is_approved", False)
        })

    return result


def get_doctor_by_id(doctor_id: str):
    doctor = mongo_db["doctors"].find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        return None

    return {
        "id": str(doctor["_id"]),
        "first_name": doctor.get("first_name"),
        "last_name": doctor.get("last_name"),
        "email": doctor.get("email"),
        "phone_number": doctor.get("phone_number"),
        "cv_url": doctor.get("cv_url"),
        "is_approved": doctor.get("is_approved", False)
    }





UPLOAD_PROFILE_DIR = "uploads/profile_images"
os.makedirs(UPLOAD_PROFILE_DIR, exist_ok=True)



def update_doctor(update_data: UpdateDoctorModel, current_user, profile_image_url: Optional[str] = None):
    updates = {k: v for k, v in update_data.dict().items() if v is not None}

    if profile_image_url:
        updates["profile_image_url"] = profile_image_url

    if not updates:
        raise HTTPException(status_code=400, detail="لا يوجد بيانات لتحديثها")

    mongo_db["doctors"].update_one({"_id": ObjectId(current_user["_id"])}, {"$set": updates})
    updated_doctor = mongo_db["doctors"].find_one({"_id": ObjectId(current_user["_id"])})
    updated_doctor["_id"] = str(updated_doctor["_id"])
    return updated_doctor



