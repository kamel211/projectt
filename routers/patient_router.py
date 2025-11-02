from fastapi import APIRouter, Depends, Header, Request
from Controller.patient_controller import (
    CreatePatientRequest,
    LoginPatientRequest,
    ChangePasswordRequest,
    UpdatePatientRequest,
    register_patient,
    login_patient,
    logout_patient,
    change_password,
    update_patient_profile,
    get_current_patient
)

router = APIRouter(prefix="/patients", tags=["Patients Auth"])

# تسجيل مريض جديد
@router.post("/register")
def register(request: CreatePatientRequest):
    return register_patient(request)


# تسجيل دخول المريض
@router.post("/login")
async def login(request: LoginPatientRequest, req: Request):
    return await login_patient(request, req)


# تسجيل خروج المريض
@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]
    return logout_patient(token)


# تغيير كلمة مرور المريض
@router.put("/change-password")
def change_patient_password(
    request_data: ChangePasswordRequest,
    current_patient: dict = Depends(get_current_patient)
):
    return change_password(request_data, current_patient)


# بيانات المريض الحالي
@router.get("/me")
def get_current_patient_info(current_patient: dict = Depends(get_current_patient)):
    return {
        "id": str(current_patient["_id"]),
        "username": current_patient["username"],
        "email": current_patient["email"],
        "first_name": current_patient["first_name"],
        "last_name": current_patient["last_name"],
        "phone_number": current_patient.get("phone_number", ""),
        "role": current_patient["role"],
        "full_name": f"{current_patient['first_name']} {current_patient['last_name']}"
    }


# تحديث بيانات المريض الحالي
@router.put("/me_update")
def update_patient_profile_endpoint(
    update_data: UpdatePatientRequest,
    current_patient: dict = Depends(get_current_patient)
):
    return update_patient_profile(update_data, current_patient)
