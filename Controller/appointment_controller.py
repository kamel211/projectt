# appointment_controller.py
from fastapi import HTTPException
from datetime import datetime, time, timedelta
from jose import jwt
from typing import List
from pydantic import BaseModel
from bson.objectid import ObjectId
from database import patients_collection, appointments_collection, doctors_collection
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException
from database import doctors_collection, appointments_collection, patients_collection

SECRET_KEY = "mysecretkey"

# -------------------- نموذج المواعيد --------------------
class AppointmentResponse(BaseModel):
    appointment_id: str
    doctor_name: str = None
    patient_name: str = None
    date_time: str
    status: str
    reason: str = None


# دالة مساعدة لتحويل ObjectId إلى string
def convert_objectid(doc):
    if not doc:
        return None
    doc = dict(doc)  # نسخ القاموس لتعديله
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc

def book_appointment(patient_email: str, doctor_id: str, date_time: datetime, reason: str = ""):
    # التأكد أن الطبيب موجود
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # البحث عن المريض باستخدام البريد
    patient = patients_collection.find_one({"email": patient_email})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # إنشاء الموعد
    appointment = {
        "doctor_id": ObjectId(doctor_id),
        "patient_id": patient["_id"],
        "date_time": date_time,
        "reason": reason,
        "status": "pending"
    }
    
    result = appointments_collection.insert_one(appointment)
    appointment["_id"] = str(result.inserted_id)
    appointment["doctor_id"] = str(appointment["doctor_id"])
    appointment["patient_id"] = str(appointment["patient_id"])
    
    return appointment

# -------------------- التحقق من التوكن --------------------
def get_user_from_token(token: str, role_required: str = None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    if role_required and payload.get("role") != role_required:
        raise HTTPException(status_code=403, detail=f"Access denied for role: {payload.get('role')}")

    return payload

# -------------------- قائمة الأطباء --------------------
def get_all_doctors():
    doctors = list(doctors_collection.find({}, {"first_name": 1, "last_name": 1, "specialty": 1}))
    result = []
    for d in doctors:
        full_name = f"{d.get('first_name', '-')}"
        if d.get("last_name"):
            full_name += f" {d['last_name']}"
        result.append({
            "id": str(d["_id"]),
            "name": full_name,
            "specialty": d.get("specialty", "")
        })
    return result

# -------------------- حجز موعد --------------------
def book_appointment(token: str, doctor_id: str, date_time: datetime, reason: str = None):
    payload = get_user_from_token(token, role_required="patient")
    patient_id = payload.get("id")  # <<< استخدم الـ _id من التوكن
    patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    now = datetime.now()
    if date_time <= now:
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")
    if date_time.time() < time(10, 0) or date_time.time() > time(16, 0):
        raise HTTPException(status_code=400, detail="Appointment must be within working hours (10:00 - 16:00)")
    if date_time.weekday() > 4:
        raise HTTPException(status_code=400, detail="Appointments allowed only Sunday-Thursday")
    if date_time.minute not in (0, 30):
        raise HTTPException(status_code=400, detail="Appointments must start at 00 or 30 minutes")

    # تحقق من وجود تضارب
    conflict = appointments_collection.find_one({
        "doctor_id": doctor_id,
        "status": {"$ne": "Cancelled"},
        "date_time": date_time
    })
    if conflict:
        raise HTTPException(status_code=400, detail="Doctor has another appointment at this time")

    new_app = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "date_time": date_time,
        "reason": reason,
        "status": "Pending"
    }
    result = appointments_collection.insert_one(new_app)
    new_app["appointment_id"] = str(result.inserted_id)
    return new_app

# -------------------- إلغاء موعد --------------------
def cancel_appointment(token: str, appointment_id: str):
    payload = get_user_from_token(token, role_required="patient")
    patient_id = payload.get("id")

    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment["patient_id"] != patient_id:
        raise HTTPException(status_code=403, detail="Not allowed to cancel this appointment")
    if appointment["status"] == "Cancelled":
        raise HTTPException(status_code=400, detail="Appointment already cancelled")
    if appointment["date_time"] < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot cancel a past appointment")

    appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": "Cancelled"}})
    return {"message": "Appointment cancelled successfully", "appointment_id": appointment_id}

# -------------------- مواعيد المريض --------------------
def get_patient_appointments(token: str) -> List[AppointmentResponse]:
    payload = get_user_from_token(token, role_required="patient")
    patient_id = payload.get("id")

    appointments = list(appointments_collection.find({"patient_id": patient_id}))
    result = []
    for app in appointments:
        doctor = doctors_collection.find_one({"_id": ObjectId(app["doctor_id"])})
        status_text = {
            "Pending": "Waiting for doctor's approval",
            "Confirmed": "Appointment confirmed",
            "Rejected": "Appointment rejected",
            "Cancelled": "Appointment cancelled"
        }.get(app["status"], app["status"])
        result.append(AppointmentResponse(
            appointment_id=str(app["_id"]),
            doctor_name=f"{doctor.get('first_name','')} {doctor.get('last_name','')}" if doctor else "Unknown",
            date_time=app["date_time"].strftime("%Y-%m-%d %H:%M"),
            status=status_text,
            reason=app.get("reason")
        ))
    return result

# -------------------- مواعيد الطبيب --------------------
def get_doctor_appointments(token: str) -> List[AppointmentResponse]:
    payload = get_user_from_token(token, role_required="doctor")
    doctor_id = payload.get("id")

    appointments = list(appointments_collection.find({"doctor_id": doctor_id}))
    result = []
    for app in appointments:
        patient = patients_collection.find_one({"_id": ObjectId(app["patient_id"])})
        result.append(AppointmentResponse(
            appointment_id=str(app["_id"]),
            patient_name=f"{patient.get('first_name','')} {patient.get('last_name','')}" if patient else "Unknown",
            date_time=app["date_time"].strftime("%Y-%m-%d %H:%M"),
            status=app["status"],
            reason=app.get("reason")
        ))
    return result

# -------------------- موافقة/رفض الطبيب --------------------
def approve_appointment(token: str, appointment_id: str, approve: bool):
    payload = get_user_from_token(token, role_required="doctor")
    doctor_id = payload.get("id")

    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment["doctor_id"] != doctor_id:
        raise HTTPException(status_code=403, detail="Not allowed to approve this appointment")
    if appointment["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Appointment already processed")

    new_status = "Confirmed" if approve else "Rejected"
    appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": new_status}})
    return {"message": "Appointment updated successfully",
            "appointment_id": appointment_id,
            "new_status": new_status}

# -------------------- الأوقات المتاحة للطبيب --------------------
def get_available_slots(doctor_id: str, date: str):
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    start_time = time(10, 0)
    end_time = time(16, 0)
    slot_duration = timedelta(minutes=30)

    current = datetime.strptime(date, "%Y-%m-%d").replace(hour=start_time.hour, minute=start_time.minute)
    end_datetime = datetime.strptime(date, "%Y-%m-%d").replace(hour=end_time.hour, minute=end_time.minute)

    existing_appointments = list(appointments_collection.find({
        "doctor_id": doctor_id,
        "status": {"$ne": "Cancelled"},
        "date_time": {"$gte": current, "$lt": end_datetime + slot_duration}
    }))
    booked_times = [app["date_time"] for app in existing_appointments]

    available_slots = []
    while current <= end_datetime:
        if all(current != bt for bt in booked_times):
            available_slots.append(current.strftime("%H:%M"))
        current += slot_duration
    return available_slots
