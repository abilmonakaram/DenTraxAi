from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class ReferringDoctor(Base):
    __tablename__ = "referring_doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    patients = relationship("Patient", back_populates="referring_doctor")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    dentrix_id = Column(String, index=True, nullable=True)
    name = Column(String, index=True)
    referring_doctor_id = Column(Integer, ForeignKey("referring_doctors.id"))

    referring_doctor = relationship("ReferringDoctor", back_populates="patients")
    productions = relationship("Production", back_populates="patient")

class Production(Base):
    __tablename__ = "productions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    amount = Column(Float, default=0.0)
    month_year = Column(String, index=True) # Format YYYY-MM
    date_recorded = Column(Date)

    patient = relationship("Patient", back_populates="productions")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
