def get_current_doctor(token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    doctor = doctors_collection.find_one({"username": username})
    if not doctor:
        raise HTTPException(status_code=401, detail="Doctor not found")
    doctor["_id"] = str(doctor["_id"])
    return doctor
