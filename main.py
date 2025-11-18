# kaaammeel


from fastapi import FastAPI
from database import *  # لو بدك تستخدم الاتصال بـ PostgreSQL و MongoDB
from routers import patient_router 
from routers import dector_router 
from fastapi.staticfiles import StaticFiles
from routers import appointment_router 
from routers import admin_router
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "🚀 Server is running with auto-reload!"}


# patient
app.include_router(patient_router.router)



app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# dector

app.include_router(dector_router.router)

# appointments
app.include_router(appointment_router.router)


app.include_router(admin_router.admin_router)  # ✅
# uvicorn main:app --reload