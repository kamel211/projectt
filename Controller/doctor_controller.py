from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from models.dector_model import Dector

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# نموذج التسجيل
class CreateDectorRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

# نموذج تسجيل الدخول
class LoginDectorRequest(BaseModel):
    username: str
    password: str

# تسجيل دكتور جديد
def registerDector(db: Session, request: CreateDectorRequest):
    existing_dector = db.query(Dector).filter(Dector.username == request.username).first()
    if existing_dector:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_dector = Dector(
        email=request.email,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        hashed_password=bcrypt_context.hash(request.password),
        phone_number=request.phone_number
    )
    db.add(new_dector)
    db.commit()
    db.refresh(new_dector)
    return {"message": "Dector registered successfully", "dector": new_dector.username}

# تسجيل الدخول
def loginDector(db: Session, request: LoginDectorRequest):
    dector = db.query(Dector).filter(Dector.username == request.username).first()
    if not dector or not bcrypt_context.verify(request.password, dector.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": f"Welcome Dr. {dector.username}", "role": dector.role}














# from fastapi import HTTPException, status
# from sqlalchemy.orm import Session
# from passlib.context import CryptContext
# from pydantic import BaseModel
# from models.dector_model import Dector

# # 🔹 لإدارة تشفير كلمة المرور
# bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # 🔹 نموذج البيانات القادمة من الطلب
# class CreateDectorRequest(BaseModel):
#     username: str
#     email: str
#     first_name: str
#     last_name: str
#     password: str
#     role: str
#     phone_number: str

# # 🔹 الدالة المسؤولة عن تسجيل دكتور جديد
# def registerDector(db: Session, create_dector_request: CreateDectorRequest):
#     # التحقق إذا كان الاسم مستخدم مسبقًا
#     existing_dector = db.query(Dector).filter(Dector.username == create_dector_request.username).first()
#     if existing_dector:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

#     # إنشاء كائن دكتور جديد
#     new_dector = Dector(
#         email=create_dector_request.email,
#         username=create_dector_request.username,
#         first_name=create_dector_request.first_name,
#         last_name=create_dector_request.last_name,
#         role=create_dector_request.role,
#         hashed_password=bcrypt_context.hash(create_dector_request.password),
#         phone_number=create_dector_request.phone_number
#     )

#     # حفظ الدكتور في قاعدة البيانات
#     db.add(new_dector)
#     db.commit()
#     db.refresh(new_dector)

#     # استجابة ناجحة
#     return {"message": "Dector registered successfully", "dector": new_dector.username}
