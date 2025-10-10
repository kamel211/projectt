from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from models.user_model import Users

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# نموذج التسجيل
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

# نموذج تسجيل الدخول
class LoginUserRequest(BaseModel):
    username: str
    password: str

# تسجيل مستخدم جديد
def registerUser(db: Session, request: CreateUserRequest):
    existing_user = db.query(Users).filter(Users.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = Users(
        email=request.email,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        hashed_password=bcrypt_context.hash(request.password),
        phone_number=request.phone_number
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user": new_user.username}

# تسجيل الدخول
def loginUser(db: Session, request: LoginUserRequest):
    user = db.query(Users).filter(Users.username == request.username).first()
    if not user or not bcrypt_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": f"Welcome {user.username}", "role": user.role}














# from fastapi import HTTPException, status
# from sqlalchemy.orm import Session
# from passlib.context import CryptContext
# from models.users_model import Users
# from pydantic import BaseModel

# bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # نموذج البيانات القادمة من المستخدم
# class CreateUserRequest(BaseModel):
#     username: str
#     email: str
#     first_name: str
#     last_name: str
#     password: str
#     role: str
#     phone_number: str

# # دالة إنشاء المستخدم
# def create_user(db: Session, create_user_request: CreateUserRequest):
#     existing_user = db.query(Users).filter(Users.username == create_user_request.username).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username already exists")

#     create_user_model = Users(
#         email=create_user_request.email,
#         username=create_user_request.username,
#         first_name=create_user_request.first_name,
#         last_name=create_user_request.last_name,
#         role=create_user_request.role,
#         hashed_password=bcrypt_context.hash(create_user_request.password),
#         phone_number=create_user_request.phone_number
#     )

#     db.add(create_user_model)
#     db.commit()
#     db.refresh(create_user_model)
#     return {"message": "User created successfully", "user": create_user_model.username}
