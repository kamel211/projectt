# admin_controller.py
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException
from bson import ObjectId
from database import doctors_collection,patients_collection,admins_collection


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

class AdminController:



    async def register(self, email: str, password: str):
        # تحقق من وجود Admin مسبقاً
        existing = await admins_collection.find_one({"email": email})
        if existing:
            raise HTTPException(status_code=400, detail="Admin already exists")

        hashed_password = bcrypt_context.hash(password)
        new_admin = {
            "email": email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "role": "admin",
            "is_active": True
        }

        result = await admins_collection.insert_one(new_admin)
        return {"id": str(result.inserted_id), "email": email}
    


    def create_access_token(self, username: str, expires_delta: timedelta = timedelta(hours=4)):
        payload = {"sub": username, "exp": datetime.utcnow() + expires_delta}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    async def login(self, email: str, password: str):
        admin = await admins_collection.find_one({"email": email})
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        if not bcrypt_context.verify(password, admin["hashed_password"]):
            raise HTTPException(status_code=401, detail="Incorrect password")

        # إنشاء توكن JWT
        payload = {"sub": email, "exp": datetime.utcnow() + timedelta(hours=4)}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}


    async def get_all_users(self):
        doctors = await doctors_collection.find().to_list(length=100)
        patients = await patients_collection.find().to_list(length=100)

        def serialize(user):
            user["_id"] = str(user["_id"])
            return user

        return {
            "doctors": [serialize(d) for d in doctors],
            "patients": [serialize(p) for p in patients]
        }

    async def update_doctor(self, doctor_id: str, is_active: bool = None, is_approved: bool = None):
        doctor = await doctors_collection.find_one({"_id": ObjectId(doctor_id)})
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        updates = {}
        if is_active is not None:
            updates["is_active"] = is_active
        if is_approved is not None:
            updates["is_approved"] = is_approved

        if updates:
            await doctors_collection.update_one({"_id": ObjectId(doctor_id)}, {"$set": updates})

        updated_doctor = await doctors_collection.find_one({"_id": ObjectId(doctor_id)})
        updated_doctor["_id"] = str(updated_doctor["_id"])
        return updated_doctor

admin_controller = AdminController()
