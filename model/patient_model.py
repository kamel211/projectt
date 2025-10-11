''' from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Users(Base):
    __tablename__ = "patient"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)

    # العلاقة مع المواعيد
    appointments = relationship("Appointment", back_populates="patient")'''
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Users(Base):
    __tablename__ = "patients"  # اسم الجدول في قاعدة البيانات
    
    # الأعمدة الأساسية
    id = Column(Integer, primary_key=True, index=True)  # مفتاح أساسي
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # الحقول الإضافية
    role = Column(String(50), default="patient")  # دور المستخدم
    phone_number = Column(String(20))  # رقم الهاتف
    
    # حقول الوقت والتاريخ
    created_at = Column(DateTime, default=datetime.utcnow)  # وقت الإنشاء
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # وقت التحديث
    is_active = Column(Boolean, default=True)  # مفعل/غير مفعل
    is_verified = Column(Boolean, default=False)  # موثق/غير موثق

    # العلاقة مع جدول المواعيد
    appointments = relationship("Appointment", back_populates="patient")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"