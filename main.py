# main.py

import logging
from Controller.patient_controller import patient_controller 
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Routers
from routers import patient_router
from routers import dector_router
from routers import appointment_router
from routers import admin_router

# إنشاء التطبيق
app = FastAPI()

# الصفحة الرئيسية
@app.get("/")
def read_root():
    return {"message": "🚀 Server is running with auto-reload!"}

# =============== Include Routers ===============
app.include_router(patient_router.router)
app.include_router(dector_router.router)
app.include_router(appointment_router.router)
app.include_router(admin_router.admin_router)

# للصور
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# =============== Logging ===============
logging.basicConfig(level=logging.INFO)

@app.on_event("startup")
async def startup_event():
    await patient_controller.startup_event()
