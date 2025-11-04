# admin_model.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class DoctorModel(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    role: str = "doctor"
    cv_url: Optional[str] = None
    is_approved: bool = False
    created_at: Optional[datetime] = None
