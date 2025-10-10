from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Users(Base):
    __tablename__ = 'patient'  # اسم الجدول الصحيح

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    role = Column(String)

    # علاقة المستخدم بالصور
    images = relationship("Images", back_populates="user")

