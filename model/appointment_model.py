from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from model.patient_model import Users
from model.doctor_model import Doctor




class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("patient.id"))
    doctor_id = Column(Integer, ForeignKey("doctor.id"))
    date_time = Column(DateTime, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default="Pending")
    user = relationship("Users", back_populates="appointments")
    doctor = relationship("Doctors", back_populates="appointments")