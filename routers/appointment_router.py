from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from Controller.patient_controller import get_current_patient
from Controller.appointment_controller import book_appointment, cancel_appointment, get_user_appointments
from model.patient_model import Users
from model.appointment_model import Appointment
from model.doctor_model import Doctors
from datetime import datetime, time

router = APIRouter(prefix="/appointments", tags=["Appointments"])

# ------------------- قائمة الدكاترة -------------------
@router.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctors).all()
    result = []
    for doc in doctors:
        result.append({
            "id": doc.id,
            "name": doc.username,
            "email": doc.email,
            "work_hours": "10:00 - 16:00",
            "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        })
    return result

# ------------------- حجز موعد -------------------
@router.post("/book")
def create_appointment(
    doctor_id: int,
    date_time: datetime,
    reason: str = None,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    """
    🔹 تحجز موعد بعد التحقق من:
    - وجود الدكتور
    - الوقت ضمن ساعات العمل 10:00-16:00
    - اليوم من الأحد إلى الخميس
    - الموعد ليس في الماضي
    - لا يوجد تداخل مع مواعيد الطبيب
    - الموعد على نصف ساعة (00 أو 30)
    """
    return book_appointment(db=db, user=user, doctor_id=doctor_id, date_time=date_time, reason=reason)

# ------------------- مواعيد المريض -------------------
@router.get("/my")
def get_my_appointments(db: Session = Depends(get_db), user: Users = Depends(get_current_patient)):
    """
    🔹 ترجع كل مواعيد المريض (Scheduled و Cancelled) مع تفاصيل الطبيب
    """
    return get_user_appointments(db=db, user=user)

# ------------------- إلغاء موعد -------------------
@router.delete("/cancel/{appointment_id}")
def cancel_user_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    """
    🔹 تلغي موعد إذا كان موجوداً ويخص المريض
    """
    return cancel_appointment(db=db, user=user, appointment_id=appointment_id)
