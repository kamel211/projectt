from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ✅ موديل إنشاء حساب جديد للدكتور
class CreateDoctorModel(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    phone_number: Optional[str]
    role: str = "doctor"
    cv_url: Optional[str] = None  # رابط السيرة الذاتية (PDF / صورة)
    is_approved: bool = False     # يتم تفعيله بعد موافقة الأدمن
    created_at: datetime = datetime.utcnow()


# ✅ موديل تسجيل الدخول
class LoginDoctorModel(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

class UpdateDoctorModel(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None
    profile_image_url: Optional[str] = None  
