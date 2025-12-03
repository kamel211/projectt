# admin_router.py
from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from Controller.admin_controller import admin_controller
from jose import jwt, JWTError

# ----------------- Models -----------------
class AdminRegisterModel(BaseModel):
    email: EmailStr
    password: str

class AdminLoginModel(BaseModel):
    email: EmailStr
    password: str

# ----------------- Router -----------------
router = APIRouter(prefix="/admin", tags=["Admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

# ----------------- Token dependency -----------------
async def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ----------------- Endpoints -----------------

@router.post("/register")
async def register_admin(admin: AdminRegisterModel):
    return await admin_controller.register(admin.email, admin.password)

@router.post("/login")
async def login_admin(admin: AdminLoginModel):
    return await admin_controller.login(admin.email, admin.password)

@router.get("/users")
async def get_users(current_admin=Depends(get_current_admin)):
    return await admin_controller.get_all_users()

@router.put("/doctor/update/{doctor_id}")
async def update_doctor_status(
    doctor_id: str,
    is_active: bool = Body(None),
    is_approved: bool = Body(None),
    current_admin=Depends(get_current_admin)
):
    return await admin_controller.update_doctor(doctor_id, is_active, is_approved)
