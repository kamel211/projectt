from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Doctors(Base):
    __tablename__ = "doctor"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)

    # العلاقة مع المواعيد
    appointments = relationship("Appointment", back_populates="doctor")
