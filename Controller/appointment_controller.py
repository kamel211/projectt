from fastapi import HTTPException
from sqlalchemy.orm import Session
from model.appointment_model import Appointment
from model.doctor_model import Doctors
from model.patient_model import Users
from datetime import datetime, time

def book_appointment(db: Session, user: Users, doctor_id: int, date_time: datetime, reason: str = None):
    # 1️⃣ التأكد من وجود الدكتور
    doctor = db.query(Doctors).filter(Doctors.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # 2️⃣ التحقق من ساعات العمل (10:00 - 16:00)
    appointment_time = date_time.time()
    if appointment_time < time(10, 0) or appointment_time > time(16, 0):
        raise HTTPException(status_code=400, detail="Appointment must be within working hours 10:00 - 16:00")

    # 3️⃣ التحقق من أيام العمل (Sunday=6, Monday=0 ... Thursday=3)
    weekday = date_time.weekday()  # 0=Monday ... 6=Sunday
    if weekday > 4:  # Friday (5) & Saturday (6) خارج أيام العمل
        raise HTTPException(status_code=400, detail="Appointments are only allowed from Sunday to Thursday")

    # 4️⃣ منع تداخل المواعيد
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date_time == date_time,
        Appointment.status != "Cancelled"
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Doctor already has an appointment at this time")

    # 5️⃣ إنشاء الموعد
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

    return new_app
