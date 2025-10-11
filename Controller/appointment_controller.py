from fastapi import HTTPException
from sqlalchemy.orm import Session
from model.appointment_model import Appointment
from model.doctor_model import Doctors
from model.patient_model import Users
from datetime import datetime

# دالة لحجز موعد
def book_appointment(db: Session, user: Users, doctor_id: int, date_time: datetime, reason: str = None):
    doctor = db.query(Doctors).filter(Doctors.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
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
