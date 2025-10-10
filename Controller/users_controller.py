from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models.users_model import Users
from pydantic import BaseModel

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# نموذج البيانات القادمة من المستخدم
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

# دالة إنشاء المستخدم
def create_user(db: Session, create_user_request: CreateUserRequest):
    existing_user = db.query(Users).filter(Users.username == create_user_request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        phone_number=create_user_request.phone_number
    )

    db.add(create_user_model)
    db.commit()
    db.refresh(create_user_model)
    return {"message": "User created successfully", "user": create_user_model.username}
