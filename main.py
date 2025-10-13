from fastapi import FastAPI
from database import *  # لو بدك تستخدم الاتصال بـ PostgreSQL و MongoDB
from routers import patient_router 

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "🚀 Server is running with auto-reload!"}

app.include_router(patient_router.router)


# uvicorn main:app --reload