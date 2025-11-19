# appointment_controller.py
from email import parser
from fastapi import HTTPException, Header
from datetime import datetime, time, timedelta
from typing import List
from pydantic import BaseModel
from bson import ObjectId
from database import appointments_collection ,patients_collection,doctors_collection
import aiosmtplib
from email.mime.text import MIMEText
import asyncio

# -------------------- إعداد SMTP للإشعارات --------------------
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_LOGIN = "9b77a8001@smtp-brevo.com"
SMTP_PASSWORD = "WSn3aDfVAKMhJwrd"
FROM_EMAIL = "Douha Sharkawi <douhasharkawi@gmail.com>"

# -------------------- نموذج المواعيد --------------------
class AppointmentResponse(BaseModel):
    appointment_id: str
    doctor_name: str = None
    patient_name: str = None
    date_time: str
    status: str
    reason: str = None

# -------------------- دوال مساعدة --------------------
def convert_objectid(doc):
    if not doc:
        return None
    doc = dict(doc)
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc

def get_user_from_token(token: str, role_required: str = None):
    # هذه الدالة تحتاج أن يكون لديك JWT
    from jose import jwt
    SECRET_KEY = "mysecretkey"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    if role_required and payload.get("role") != role_required:
        raise HTTPException(status_code=403, detail=f"Access denied for role: {payload.get('role')}")
    return payload

# -------------------- إرسال الإيميل --------------------
def notify_patient_email(patient_email: str, doctor_name: str, date_time: str, approved: bool):
    subject = f"تحديث حول موعدك مع الدكتور {doctor_name}"
    status_text = "تمت الموافقة على موعدك " if approved else "تم رفض موعدك "
    content = (
        f"مرحباً،\n\n"
        f"{status_text}\n"
        f"تاريخ ووقت الموعد: {date_time}\n"
        f"شكراً لاستخدامك نظامنا للحجز.\n\n"
        f"مع تحيات فريقنا."
    )
    asyncio.create_task(send_email_async(patient_email, subject, content))

async def send_email_async(recipient: str, subject: str, content: str):
    message = MIMEText(content, "plain", "utf-8")
    message["From"] = FROM_EMAIL
    message["To"] = recipient
    message["Subject"] = subject
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_LOGIN,
            password=SMTP_PASSWORD,
        )
        print(f"Email sent to {recipient}")
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")

# -------------------- حجز موعد --------------------
def book_appointment(token: str, doctor_id: str, date_time: datetime, reason: str = None):
    payload = get_user_from_token(token, role_required="patient")
    patient_id = payload.get("id")
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

    # ❌ تحقق إذا المريض لديه موعد بالفعل في نفس الوقت
    existing = appointments_collection.find_one({
        "patient_id": patient_id,
        "status": {"$ne": "Cancelled"},
        "date_time": date_time
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already have an appointment at this time")

    # ❌ تحقق إذا الطبيب لديه موعد في نفس الوقت
    conflict = appointments_collection.find_one({
        "doctor_id": doctor_id,
        "status": {"$ne": "Cancelled"},
        "date_time": date_time
    })
    if conflict:
        raise HTTPException(status_code=400, detail="Doctor has another appointment at this time")

    # إعداد المستند
    new_app = {
        "patient_id": str(patient["_id"]),
        "doctor_id": str(doctor["_id"]),
        "date_time": date_time.isoformat(),
        "reason": reason,
        "status": "Pending"
    }
    result = appointments_collection.insert_one(new_app)
    
    # تحويل كل ObjectId إلى string قبل الإرجاع
    response = {
        "appointment_id": str(result.inserted_id),
        "patient_id": new_app["patient_id"],
        "doctor_id": new_app["doctor_id"],
        "date_time": new_app["date_time"],
        "reason": new_app["reason"],
        "status": new_app["status"]
    }
    return response


async def approve_appointment(token: str, appointment_id: str, approve: bool):
    # التحقق من هوية الدكتور
    payload = get_user_from_token(token, role_required="doctor")
    doctor_id = payload.get("id")

    # جلب الموعد
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["doctor_id"] != doctor_id:
        raise HTTPException(status_code=403, detail="Not allowed to approve this appointment")

    if appointment["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Appointment already processed")

    # تحديد الحالة الجديدة
    new_status = "Confirmed" if approve else "Rejected"

    # تحديث الموعد في MongoDB
    appointments_collection.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": new_status}}
    )

    # ------------------------
    #  تجهيز بيانات الإيميل
    # ------------------------
    patient = patients_collection.find_one({"_id": ObjectId(appointment["patient_id"])})
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})

    # معالجة التاريخ String → datetime
    raw_date = appointment["date_time"]

    # إزالة Z إذا موجودة (بعض الأنظمة ترجع ISO مثل: "2025-11-18T13:30:00Z")
    clean_date = raw_date.replace("Z", "")

    # التحويل الصحيح
    date_time = datetime.fromisoformat(clean_date)

    # إرسال الإيميل إذا كانت البيانات كاملة
    if patient and doctor:
       notify_patient_email(
                patient_email=patient["email"],
                doctor_name=f"{doctor.get('first_name', '')} {doctor.get('last_name', '')}",
                date_time=date_time.strftime("%Y-%m-%d %H:%M"),
                approved=approve
)


    # نص الحالة
    status_display = {
        "Confirmed": "تمت الموافقة",
        "Rejected": "تم الرفض",
        "Completed": "تم الإنجاز",
        "Cancelled": "تم الإلغاء"
    }.get(new_status, new_status)

    return {
        "message": "Appointment updated successfully",
        "appointment_id": appointment_id,
        "new_status": new_status,
        "display_status": status_display
    }
# -------------------- مواعيد المريض --------------------
def get_patient_appointments(token: str) -> List[AppointmentResponse]:
    payload = get_user_from_token(token, role_required="patient")
    patient_id = payload.get("id")
    appointments = list(appointments_collection.find({"patient_id": patient_id}))
    result = []
    for app in appointments:
        doctor = doctors_collection.find_one({"_id": ObjectId(app["doctor_id"])})
        
        # تحويل تاريخ ISO string إلى datetime
        date_obj = datetime.fromisoformat(app["date_time"]) if isinstance(app["date_time"], str) else app["date_time"]

        status_text = {
            "Pending": "Waiting for doctor's approval",
            "Confirmed": "Appointment confirmed",
            "Rejected": "Appointment rejected",
            "Cancelled": "Appointment cancelled"
        }.get(app["status"], app["status"])
        
        result.append(AppointmentResponse(
            appointment_id=str(app["_id"]),
            doctor_name=f"{doctor.get('first_name','')} {doctor.get('last_name','')}" if doctor else "Unknown",
            date_time=date_obj.strftime("%Y-%m-%d %H:%M"),
            status=status_text,
            reason=app.get("reason")
        ))
    return result


# -------------------- مواعيد الطبيب --------------------
from datetime import datetime

def get_doctor_appointments(token: str) -> List[AppointmentResponse]:
    payload = get_user_from_token(token, role_required="doctor")
    doctor_id = payload.get("id")
    appointments = list(appointments_collection.find({"doctor_id": doctor_id}))
    result = []

    for app in appointments:
        patient = patients_collection.find_one({"_id": ObjectId(app["patient_id"])})

        # التأكد من نوع التاريخ
        date_time_obj = app["date_time"]
        if isinstance(date_time_obj, str):
            date_time_obj = datetime.fromisoformat(date_time_obj)  # تحويل من ISO string إلى datetime

        result.append(AppointmentResponse(
            appointment_id=str(app["_id"]),
            patient_name=f"{patient.get('first_name','')} {patient.get('last_name','')}" if patient else "Unknown",
            date_time=date_time_obj.strftime("%Y-%m-%d %H:%M") if date_time_obj else "-",
            status=app.get("status", ""),
            reason=app.get("reason")
        ))
    return result


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


def cancel_appointment(token: str, appointment_id: str):
    payload = get_user_from_token(token, role_required="patient")
    patient_id = payload.get("id")

    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["patient_id"] != patient_id:
        raise HTTPException(status_code=403, detail="You cannot cancel this appointment")

    if appointment["status"] in ["Cancelled", "Rejected"]:
        raise HTTPException(status_code=400, detail="Appointment already cancelled")

    appointments_collection.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": "Cancelled"}}
    )

    return {"message": "Appointment cancelled successfully"}
def update_expired_appointments():
    now = datetime.now()
    expired = appointments_collection.find({"status": {"$in": ["Confirmed", "Pending"]}})
    for app in expired:
        app_time = app["date_time"]
        if isinstance(app_time, str):
            app_time = datetime.fromisoformat(app_time)
        if app_time < now:
            appointments_collection.update_one(
                {"_id": app["_id"]},
                {"$set": {"status": "Cancelled"}}
            )



# -------------------- تعليم الموعد كمكتمل --------------------
def complete_appointment(token: str, appointment_id: str):
    payload = get_user_from_token(token, role_required="doctor")
    doctor_id = payload.get("id")

    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment["doctor_id"] != doctor_id:
        raise HTTPException(status_code=403, detail="Not allowed to complete this appointment")

    if appointment["status"] != "Confirmed":
        raise HTTPException(status_code=400, detail="Only confirmed appointments can be completed")

    appointments_collection.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": "Completed", "completed_at": datetime.now()}}
    )

    return {"message": "Appointment marked as completed", "appointment_id": appointment_id, "new_status": "Completed"}




async def get_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    return authorization[7:]
