from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from Controller.appointment_controller import (
    get_all_doctors,
    book_appointment,
    cancel_appointment,
    get_patient_appointments,
    get_doctor_appointments,
    approve_appointment,
    get_available_slots
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/patients/login")


# 🧑‍⚕️ قائمة الأطباء
@router.get("/doctors")
def list_doctors(token: str = Depends(oauth2_scheme)):
    return get_all_doctors()


# 📅 حجز موعد جديد
@router.post("/book")
def create_appointment(doctor_id: str, date_time: datetime, reason: str = "", token: str = Depends(oauth2_scheme)):
    return book_appointment(token, doctor_id, date_time, reason)


# ❌ إلغاء الموعد
@router.post("/cancel/{appointment_id}")
def cancel(appointment_id: str, token: str = Depends(oauth2_scheme)):
    return cancel_appointment(token, appointment_id)


# 🧍‍♂️ مواعيد المريض
@router.get("/my-appointments")
def my_appointments(token: str = Depends(oauth2_scheme)):
    return get_patient_appointments(token)


# 🧑‍⚕️ مواعيد الطبيب
@router.get("/doctor-appointments")
def doctor_appointments(token: str = Depends(oauth2_scheme)):
    return get_doctor_appointments(token)


# 🩺 موافقة أو رفض الموعد
@router.post("/approve/{appointment_id}")
def approve(appointment_id: str, approve: bool = True, token: str = Depends(oauth2_scheme)):
    return approve_appointment(token, appointment_id, approve)


# 🕓 عرض الأوقات المتاحة للطبيب
@router.get("/available-slots/{doctor_id}")
def available_slots(doctor_id: str, date: str, token: str = Depends(oauth2_scheme)):
    return get_available_slots(doctor_id, date)
