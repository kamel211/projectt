from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Appointment(BaseModel):
    appointment_id: Optional[str] = None      # بديل id
    user_id: str                               # بديل ForeignKey(patient)
    doctor_id: str                             # بديل ForeignKey(doctor)
    date_time: datetime                        # نفس الشي
    status: str = "Scheduled"                  # نفس default
    reason: Optional[str] = None               # خيار إضافي (إذا بدك)

    class Config:
        orm_mode = True
