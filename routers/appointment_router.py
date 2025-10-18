from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import List
from core.auth_utils import get_user_id_from_token  # دالة JWT
from database import appointments_collection, doctors_collection, patients_collection

router = APIRouter(prefix="/appointments", tags=["Appointments"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ------------------- قائمة الدكاترة -------------------
@router.get("/doctors")
def list_doctors(token: str = Depends(oauth2_scheme)):
    doctors = []
    for doc in doctors_collection.find({"is_active": True}):
        doctors.append({
            "id": str(doc["_id"]),
            "full_name": f"{doc['first_name']} {doc['last_name']}",
            "email": doc.get("email", ""),
            "work_hours": doc.get("work_hours", "10:00-16:00"),
            "days": doc.get("work_days", ["Sunday","Monday","Tuesday","Wednesday","Thursday"])
        })
    return doctors

# ------------------- حجز موعد -------------------
@router.post("/book")
def create_appointment(doctor_id: str, date_time: datetime, reason: str = "", token: str = Depends(oauth2_scheme)):
    user_id = get_user_id_from_token(token)
    patient = patients_collection.find_one({"_id": ObjectId(user_id)})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # التحقق من doctor_id
    try:
        doc_obj_id = ObjectId(doctor_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid doctor_id")

    doctor = doctors_collection.find_one({"_id": doc_obj_id})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # التحقق من الوقت
    if date_time < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book in the past")

    appointment = {
        "doctor_id": str(doc_obj_id),
        "patient_id": str(patient["_id"]),
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "date_time": date_time,
        "reason": reason,
        "status": "Scheduled"
    }

    result = appointments_collection.insert_one(appointment)
    return {"message": "Appointment booked successfully", "appointment_id": str(result.inserted_id)}


# ------------------ جلب المواعيد لدكتور معين ------------------
@router.get("/doctor/{doctor_id}/appointments")
async def get_appointments_for_doctor(doctor_id: str, token: str = Depends(oauth2_scheme)):
    try:
        doctor_obj_id = ObjectId(doctor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid doctor_id")

    # جلب كل المواعيد الخاصة بهذا الدكتور
    appointments = list(appointments_collection.find({"doctor_id": doctor_id}))

    result = []
    for appt in appointments:
        patient_id = appt.get("patient_id")  # لاحظ تغيير user_id → patient_id
        patient_name = "غير معروف"
        if patient_id:
            patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
            if patient:
                patient_name = f"{patient.first_name} {patient.last_name}"
        result.append({
            "_id": str(appt["_id"]),
            "patient_id": patient_id,
            "patient_name": patient_name,
            "date_time": appt["date_time"].isoformat() if hasattr(appt["date_time"], "isoformat") else str(appt["date_time"]),
            "status": appt.get("status", "Unknown"),
            "reason": appt.get("reason", "-")
        })
    return result

# ------------------- إلغاء موعد -------------------
@router.delete("/cancel/{appointment_id}")
def cancel_appointment(appointment_id: str, token: str = Depends(oauth2_scheme)):
    user_id = get_user_id_from_token(token)
    try:
        appt_obj_id = ObjectId(appointment_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid appointment_id")

    appointment = appointments_collection.find_one({"_id": appt_obj_id, "patient_id": user_id})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointments_collection.update_one({"_id": appt_obj_id}, {"$set": {"status": "Cancelled"}})
    return {"message": "Appointment cancelled successfully"}
