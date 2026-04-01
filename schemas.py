from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class ReferringDoctorBase(BaseModel):
    name: str

class ReferringDoctorCreate(ReferringDoctorBase):
    pass

class ReferringDoctor(ReferringDoctorBase):
    id: int
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class PatientBase(BaseModel):
    name: str
    dentrix_id: Optional[str] = None

class PatientCreate(PatientBase):
    referring_doctor_id: Optional[int] = None

class Patient(PatientBase):
    id: int
    referring_doctor_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class ProductionBase(BaseModel):
    amount: float
    month_year: str
    date_recorded: date

class ProductionCreate(ProductionBase):
    patient_id: int

class Production(ProductionBase):
    id: int
    patient_id: int

    class Config:
        from_attributes = True
