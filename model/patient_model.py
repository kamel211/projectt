
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from model.appointment_model import Appointment

class Users(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    role = Column(String(50), default="patient")
    phone_number = Column(String(20))
    
    profile_image = Column(String(500), nullable=True)  # الصورة اختيارية
    is_active = Column(Boolean, default=True)
    
    appointments = relationship("Appointment", back_populates="patient")

