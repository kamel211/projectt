from database import mongo_db
from bson import ObjectId
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr
from typing import List

doctors_collection = mongo_db["doctors"]
admins_collection = mongo_db["admins"]

# =========================
# Admin Models
class AdminCreateModel(BaseModel):
    email: EmailStr
    username: str
    password: str

class AdminLoginModel(BaseModel):
    email: EmailStr
    password: str

# تحقق إذا فيه Admin
def is_admin_exists() -> bool:
    return admins_collection.count_documents({}) > 0

# إنشاء حساب Admin إذا ما فيه حساب
def create_admin(admin: AdminCreateModel):
    if is_admin_exists():
        raise HTTPException(status_code=403, detail="لا يمكنك إنشاء أكثر من حساب Admin")
    
    result = admins_collection.insert_one({
        "email": admin.email,
        "username": admin.username,
        "password": admin.password
    })
    return {"message": "تم إنشاء حساب Admin بنجاح ✅", "id": str(result.inserted_id)}

# تسجيل دخول Admin
def login_admin(admin: AdminLoginModel):
    account = admins_collection.find_one({"email": admin.email})
    if not account:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    if account["password"] != admin.password:
        raise HTTPException(status_code=401, detail="كلمة المرور خاطئة")
    return {"message": f"تم تسجيل الدخول بنجاح كـ Admin: {account['username']}"}

# =========================
# Doctors logic
def doctor_serializer(doctor) -> dict:
    return {
        "id": str(doctor["_id"]),
        "username": doctor["username"],
        "email": doctor["email"],
        "first_name": doctor["first_name"],
        "last_name": doctor["last_name"],
        "phone_number": doctor.get("phone_number", ""),
        "role": doctor.get("role", "doctor"),
        "cv_url": doctor.get("cv_url", ""),
        "is_approved": doctor.get("is_approved", False),
        "created_at": doctor.get("created_at")
    }

def get_pending_doctors() -> List[dict]:
    pending = doctors_collection.find({"is_approved": False})
    return [doctor_serializer(doc) for doc in pending]

def approve_doctor(doctor_id: str) -> dict:
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctors_collection.update_one({"_id": ObjectId(doctor_id)}, {"$set": {"is_approved": True}})
    return {"message": f"Doctor {doctor['first_name']} {doctor['last_name']} approved ✅"}

def reject_doctor(doctor_id: str) -> dict:
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctors_collection.delete_one({"_id": ObjectId(doctor_id)})
    return {"message": f"Doctor {doctor['first_name']} {doctor['last_name']} rejected ❌"}
