from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from Controller.patient_controller import get_current_patient
from Controller.appointment_controller import book_appointment
from model.patient_model import Users
from model.appointment_model import Appointment
from model.doctor_model import Doctors
from datetime import datetime

router = APIRouter(prefix="/appointments", tags=["Appointments"])

# قائمة الدكاترة
@router.get("/doctors")
def list_doctors(db: Session = Depends(get_db)):
    doctors = db.query(Doctors).all()
    return [{"id": doc.id, "name": doc.username, "email": doc.email} for doc in doctors]

# حجز موعد
@router.post("/book")
def create_appointment(
    doctor_id: int,
    date_time: datetime,
    reason: str = None,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    new_app = book_appointment(db=db, user=user, doctor_id=doctor_id, date_time=date_time, reason=reason)
    return {"message": "Appointment booked successfully", "appointment": new_app}

# مواعيد المستخدم
@router.get("/my")
def get_my_appointments(db: Session = Depends(get_db), user: Users = Depends(get_current_patient)):
    return db.query(Appointment).filter(Appointment.user_id==user.id).all()

# إلغاء موعد
@router.delete("/cancel/{appointment_id}")
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db), user: Users = Depends(get_current_patient)):
    appmnt = db.query(Appointment).filter(Appointment.id==appointment_id, Appointment.user_id==user.id).first()
    if not appmnt:
        return {"error": "Appointment not found"}
    appmnt.status = "Cancelled"
    db.commit()
    return {"message": "Appointment cancelled successfully"}
