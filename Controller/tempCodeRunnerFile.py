
def login_doctor(request_data: LoginDoctorRequest, request: Request):
    doctor = doctors_collection.find_one({"username": request_data.username})
    if not doctor or not bcrypt_context.verify(request_data.password, doctor["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not doctor.get("is_active", True):
        raise HTTPException(status_code=400, detail="الحساب غير مفعل. يرجى التواصل مع الإدارة.")

    token = create_access_token(doctor["username"], str(doctor["_id"]))
    return {
        "message": f"Welcome Dr. {doctor['first_name']}!",
        "access_token": token,
        "token_type": "bearer",
        "doctor_id": str(doctor["_id"]),
        "doctor_data": {
            "username": doctor["username"],
            "email": doctor["email"],
            "full_name": f"{doctor['first_name']} {doctor['last_name']}",
            "role": doctor["role"],
            "appointments": doctor.get("appointments", [])
        }
    }
