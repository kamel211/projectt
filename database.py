# database.py

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

MONGO_URL = "mongodb+srv://kamelbataineh:Kamel123@cluster0.cf0rmeu.mongodb.net/university_project?retryWrites=true&w=majority&appName=Cluster0"

try:
    # إنشاء الاتصال باستخدام Motor
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    
    # اختيار قاعدة البيانات
    mongo_db = mongo_client["university_project"]
    
    # اختيار الـ Collections
    doctors_collection = mongo_db["doctors"]
    appointments_collection = mongo_db["appointments"]
    patients_collection = mongo_db["patients"]
    otp_collection = mongo_db["otp_storage"]

    print("✅ Connected to MongoDB successfully!")

except ConnectionFailure as e:
    print("❌ MongoDB connection failed:", e)
except Exception as e:
    print("❌ MongoDB unknown error:", e)
