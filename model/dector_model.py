from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Dector(Base):
    __tablename__ = 'dector' 

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(String)
    phone_number = Column(String)

    images = relationship("Images", back_populates="dector")
