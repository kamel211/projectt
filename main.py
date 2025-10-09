from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import Base
from database import engine
from routers import signup, login, users
import cloudinary
from routers.images import router as images_router  # تأكدي أن المسار صحيح
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

app = FastAPI(
    title="Breast Clinic API",
    description="API لإدارة عيادة أورام الثدي مع رفع الصور وتحليل الذكاء الاصطناعي",
    version="1.0.0"
)

# إعداد CORS للتواصل مع الواجهة الأمامية
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # لاحقًا يمكن تحديد دومين الواجهة الأمامية فقط
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# إعداد Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dbyscbeyc"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "995823248629455"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "Nr4xisZ1yy_fvwWPTq_hX_C7gao")
)

# إنشاء الجداول في قاعدة البيانات
Base.metadata.create_all(bind=engine)

# تسجيل الـ routers
app.include_router(signup.router)    # تسجيل مستخدم جديد
app.include_router(login.router)     # تسجيل الدخول والحصول على توكن
app.include_router(users.router)     # صفحة المستخدم + عرض الصور + تغيير كلمة السر
app.include_router(images_router)    # رفع الصور واسترجاعها

# مسار أساسي للتحقق من عمل الخادم
@app.get("/")
async def root():
    return {"message": "API is working!"}

# مسار لفحص صحة الخادم
@app.get("/health")
async def health_check():
    return {"status": "hi"}  