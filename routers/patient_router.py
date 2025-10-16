from fastapi import APIRouter, Depends, Header, Request
from Controller.patient_controller import (
    CreateUserRequest,
    LoginUserRequest,
    ChangePasswordRequest,
    UpdatePatientRequest,
    register_user,
    login_user,
    logout_user,
    change_password,
    update_patient_profile,
    get_current_patient
)

router = APIRouter(prefix="/patients", tags=["Patients Auth"])

# تسجيل مريض جديد
@router.post("/register")
def register(request: CreateUserRequest):
    return register_user(request)

# تسجيل الدخول للمريض
@router.post("/login")
def login(request: LoginUserRequest, req: Request):
    return login_user(request, req)

# تسجيل الخروج للمريض
@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]
    return logout_user(token)

# تغيير كلمة المرور
@router.put("/change-password")
def change_patient_password(
    request_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_patient)
):
    return change_password(request_data, current_user)

# بيانات المستخدم الحالي
@router.get("/me")
def get_current_patient_info(current_user: dict = Depends(get_current_patient)):
    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "email": current_user["email"],
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"],
        "phone_number": current_user.get("phone_number", ""),
        "role": current_user["role"],
        "full_name": f"{current_user['first_name']} {current_user['last_name']}"
    }

# تحديث بيانات المريض
@router.put("/profile")
def update_patient_profile_endpoint(
    update_data: UpdatePatientRequest,
    current_user: dict = Depends(get_current_patient)
):
    return update_patient_profile(update_data, current_user)


###
###
###
###
###
###
###
###
###
###
###
###
###
###
###
###


'''from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from database import get_db
from Controller import patient_controller
from Controller.patient_controller import ChangePasswordRequest, changePassword, get_current_patient
from model.patient_model import Users

router = APIRouter(prefix="/users", tags=["Users Auth"])

# تسجيل مستخدم جديد
@router.post("/register")
def register(request: patient_controller.CreateUserRequest, db: Session = Depends(get_db)):
    return patient_controller.registerUser(db, request)

# تسجيل الدخول
@router.post("/login")
def login(request: patient_controller.LoginUserRequest, db: Session = Depends(get_db), req: Request = None):
    return patient_controller.loginUser(db, request, req)

# تسجيل الخروج
@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]
    return patient_controller.logoutUser(token)

# تغيير كلمة المرور
@router.put("/change-password")
def change_password(
    request_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    return changePassword(request_data, db, user)
'''

'''
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from database import get_db
from Controller.patient_controller import (
    CreateUserRequest, 
    LoginUserRequest, 
    ChangePasswordRequest, 
    UpdatePatientRequest,
    register_user, 
    login_user, 
    logout_user, 
    change_password,
    update_patient_profile,
    get_current_patient
)
from model.patient_model import Users

router = APIRouter(prefix="/patients", tags=["Patients Auth"])

# تسجيل مريض جديد
@router.post("/register")
def register(request: CreateUserRequest, db: Session = Depends(get_db)):
    return register_user(db, request)

# تسجيل الدخول للمريض
@router.post("/login")
def login(request: LoginUserRequest, db: Session = Depends(get_db), req: Request = None):
    return login_user(db, request, req)

# تسجيل الخروج للمريض
@router.post("/logout")
def logout(Authorization: str = Header(...)):
    token = Authorization.split(" ")[1]
    return logout_user(token)

# تغيير كلمة المرور للمريض
@router.put("/change-password")
def change_patient_password(
    request_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    return change_password(request_data, db, user)

# الحصول على بيانات المريض الحالي
@router.get("/me")
def get_current_patient_info(user: Users = Depends(get_current_patient)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role
    }

# تحديث بيانات المريض
@router.put("/profile")
def update_patient_profile_endpoint(
    update_data: UpdatePatientRequest,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    return update_patient_profile(update_data, db, user)
'''
<<<<<<< HEAD

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session
from database import get_db
from Controller.patient_controller import (
    CreateUserRequest, 
    LoginUserRequest, 
    ChangePasswordRequest, 
    UpdatePatientRequest,
    register_user, 
    login_user, 
    logout_user, 
    change_password,
    update_patient_profile,
    get_current_patient
)
from model.patient_model import Users
=======
>>>>>>> a95bd7cc0af2808d0540dd673dc45f876e4edea0

####
####
####
####
####
####
####
####
####
####
####
####
####
####
####
####
####
####
####
####
####
####
# from fastapi import APIRouter, Depends, Header, Request
# from sqlalchemy.orm import Session
# from database import get_db
# from Controller.patient_controller import (
#     CreateUserRequest, 
#     LoginUserRequest, 
#     ChangePasswordRequest, 
#     UpdatePatientRequest,
#     register_user, 
#     login_user, 
#     logout_user, 
#     change_password,
#     update_patient_profile,
#     get_current_patient
# )
# from model.patient_model import Users

# router = APIRouter(prefix="/patients", tags=["Patients Auth"])

# # تسجيل مريض جديد
# @router.post("/register")
# def register(request: CreateUserRequest, db: Session = Depends(get_db)):
#     return register_user(db, request)

# # تسجيل الدخول للمريض
# @router.post("/login")
# def login(request: LoginUserRequest, db: Session = Depends(get_db), req: Request = None):
#     return login_user(db, request, req)

# # تسجيل الخروج للمريض
# @router.post("/logout")
# def logout(Authorization: str = Header(...)):
#     token = Authorization.split(" ")[1]
#     return logout_user(token)

# # تغيير كلمة المرور للمريض
# @router.put("/change-password")
# def change_patient_password(
#     request_data: ChangePasswordRequest,
#     db: Session = Depends(get_db),
#     user: Users = Depends(get_current_patient)
# ):
#     return change_password(request_data, db, user)

<<<<<<< HEAD
# تحديث بيانات المريض
@router.put("/profile")
def update_patient_profile_endpoint(
    update_data: UpdatePatientRequest,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_patient)
):
    return update_patient_profile(update_data, db, user)
=======
# # الحصول على بيانات المريض الحالي
# @router.get("/me")
# def get_current_patient_info(user: Users = Depends(get_current_patient)):
#     return {
#         "id": user.id,
#         "username": user.username,
#         "email": user.email,
#         "first_name": user.first_name,
#         "last_name": user.last_name,
#         "phone_number": user.phone_number,
#         "role": user.role,
#         "full_name": user.get_full_name()
#     }

# # تحديث بيانات المريض
# @router.put("/profile")
# def update_patient_profile_endpoint(
#     update_data: UpdatePatientRequest,
#     db: Session = Depends(get_db),
#     user: Users = Depends(get_current_patient)
# ):
#     return update_patient_profile(update_data, db, user)
# ''
>>>>>>> a95bd7cc0af2808d0540dd673dc45f876e4edea0
