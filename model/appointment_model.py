from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from database import Base
from model.patient_model import Users
from model.doctor_model import Doctors


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("patient.id"))
    doctor_id = Column(Integer)
    date_time = Column(DateTime)
    status = Column(String)

    # العلاقة مع المريض
    patient = relationship("Users", back_populates="appointments")
    #العلاقه مع الدكتور 
    doctor = relationship("Doctors", back_populates="appointments")

 