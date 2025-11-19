
# # -------------------- حجز موعد --------------------
# def book_appointment(token: str, doctor_id: str, date_time: datetime, reason: str = None):
#     payload = get_user_from_token(token, role_required="patient")
#     patient_id = payload.get("id")  # <<< استخدم الـ _id من التوكن
#     patient = patients_collection.find_one({"_id": ObjectId(patient_id)})
#     doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})

#     if not patient:
#         raise HTTPException(status_code=404, detail="Patient not found")
#     if not doctor:
#         raise HTTPException(status_code=404, detail="Doctor not found")

#     now = datetime.now()
#     if date_time <= now:
#         raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")
#     if date_time.time() < time(10, 0) or date_time.time() > time(16, 0):
#         raise HTTPException(status_code=400, detail="Appointment must be within working hours (10:00 - 16:00)")
#     if date_time.weekday() > 4:
#         raise HTTPException(status_code=400, detail="Appointments allowed only Sunday-Thursday")
#     if date_time.minute not in (0, 30):
#         raise HTTPException(status_code=400, detail="Appointments must start at 00 or 30 minutes")

#     # تحقق من وجود تضارب
#     conflict = appointments_collection.find_one({
#         "doctor_id": doctor_id,
#         "status": {"$ne": "Cancelled"},
#         "date_time": date_time
#     })
#     if conflict:
#         raise HTTPException(status_code=400, detail="Doctor has another appointment at this time")

#     new_app = {
#         "patient_id": patient_id,
#         "doctor_id": doctor_id,
#         "date_time": date_time,
#         "reason": reason,
#         "status": "Pending"
#     }
#     result = appointments_collection.insert_one(new_app)
#     new_app["appointment_id"] = str(result.inserted_id)
#     return new_app
