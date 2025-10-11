from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from Controller.patient_controller import get_current_patient
from Controller.appointment_controller import book_appointment
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

# ------------------- حجز موعد مع التحقق -------------------
@router.post("/book")
def create_appointment(
    doctor_id: int,
    date_time: datetime,
    reason: str = None,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    # التحقق من وجود الدكتور
    doctor = db.query(Doctors).filter(Doctors.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # التحقق من ساعات العمل
    appointment_time = date_time.time()
    if appointment_time < time(10, 0) or appointment_time > time(16, 0):
        raise HTTPException(status_code=400, detail="Appointment must be within working hours 10:00 - 16:00")

    # التحقق من أيام العمل (Sunday-Thursday)
    weekday = date_time.weekday()  # 0=Monday ... 6=Sunday
    if weekday > 4:  # Friday (5) & Saturday (6)
        raise HTTPException(status_code=400, detail="Appointments are only allowed from Sunday to Thursday")

    # منع تداخل المواعيد
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date_time == date_time,
        Appointment.status != "Cancelled"
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Doctor already has an appointment at this time")

    # إنشاء الموعد
    new_app = Appointment(
        user_id=user.id,
        doctor_id=doctor_id,
        date_time=date_time,
        reason=reason,
        status="Scheduled"
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return {"message": "Appointment booked successfully", "appointment": new_app}

# ------------------- مواعيد المستخدم -------------------
@router.get("/my")
def get_my_appointments(db: Session = Depends(get_db), user: Users = Depends(get_current_patient)):
    return db.query(Appointment).filter(Appointment.user_id==user.id).all()

# ------------------- إلغاء موعد -------------------
@router.delete("/cancel/{appointment_id}")
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db), user: Users = Depends(get_current_patient)):
    appmnt = db.query(Appointment).filter(Appointment.id==appointment_id, Appointment.user_id==user.id).first()
    if not appmnt:
        return {"error": "Appointment not found"}
    appmnt.status = "Cancelled"
    db.commit()
    return {"message": "Appointment cancelled successfully"}
