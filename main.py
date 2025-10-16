from fastapi import FastAPI
from database import *  # لو بدك تستخدم الاتصال بـ PostgreSQL و MongoDB
from routers import patient_router 
from routers import dector_router 

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "🚀 Server is running with auto-reload!"}


# patient
app.include_router(patient_router.router)




# dector

app.include_router(dector_router.router)


# uvicorn main:app --reload