from fastapi import APIRouter, status
from core.dependencies import db_dependency
from controllers import dector_controller as dectorController

router = APIRouter(prefix="/dector", tags=["Dector"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_dector(request: dectorController.CreateDectorRequest, db: db_dependency):
    return dectorController.registerDector(db, request)

@router.post("/login")
async def login_dector(request: dectorController.LoginDectorRequest, db: db_dependency):
    return dectorController.loginDector(db, request)
