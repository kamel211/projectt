from fastapi import APIRouter, status
from core.dependencies import db_dependency
from controllers.signup_controller import create_user_controller, CreateUserRequest

router = APIRouter(
    prefix="/signup",
    tags=["Signup"]
)

# تسجيل المستخدم الجديد
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    return create_user_controller(db, create_user_request)
