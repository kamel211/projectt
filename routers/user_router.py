from fastapi import APIRouter, status
from core.dependencies import db_dependency
from controllers import user_controller as userController

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: userController.CreateUserRequest, db: db_dependency):
    return userController.registerUser(db, request)

@router.post("/login")
async def login_user(request: userController.LoginUserRequest, db: db_dependency):
    return userController.loginUser(db, request)
