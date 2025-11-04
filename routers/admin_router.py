from fastapi import APIRouter
from typing import List
from Controller.admin_controller import (
    get_pending_doctors, approve_doctor, reject_doctor,
    create_admin, login_admin, AdminCreateModel, AdminLoginModel,is_admin_exists
)

admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# ---------- Admin Routes ----------
@admin_router.post("/create")
def api_create_admin(admin: AdminCreateModel):
    return create_admin(admin)

@admin_router.post("/login")
def api_login_admin(admin: AdminLoginModel):
    return login_admin(admin)


@admin_router.get("/check")
def api_check_admin():
    exists = is_admin_exists()
    return {"exists": exists}

# ---------- Doctors Routes ----------
@admin_router.get("/pending-doctors", response_model=List[dict])
def api_get_pending_doctors():
    return get_pending_doctors()

@admin_router.put("/approve-doctor/{doctor_id}")
def api_approve_doctor(doctor_id: str):
    return approve_doctor(doctor_id)

@admin_router.put("/reject-doctor/{doctor_id}")
def api_reject_doctor(doctor_id: str):
    return reject_doctor(doctor_id)
