import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas

def process_csv_file(file_path: str, db: Session):
    # This is a sample ingestion function assuming standard columns
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return {"error": f"Failed to read CSV: {str(e)}"}

    # Clean column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Expected columns logic (very flexible for now)
    # let's assume columns roughly like: 'patient name', 'dentrix id', 'referred by', 'production amount', 'date'
    
    records_added = 0
    for _, row in df.iterrows():
        dr_name = str(row.get('referred by', 'Unknown')).strip()
        patient_name = str(row.get('patient name', 'Unknown')).strip()
        dentrix_id = str(row.get('dentrix id', ''))
        
        # Clean currency to float
        amount_str = str(row.get('production amount', '0')).replace('$', '').replace(',', '')
        try:
            amount = float(amount_str)
        except ValueError:
            amount = 0.0
        
        # Parse date
        date_str = str(row.get('date', datetime.today().strftime('%Y-%m-%d')))
        try:
            date_obj = pd.to_datetime(date_str).date()
            month_year = date_obj.strftime("%Y-%m")
        except:
            date_obj = datetime.today().date()
            month_year = date_obj.strftime("%Y-%m")
            
        if dr_name == 'nan' or dr_name == '':
            dr_name = 'Unknown'

        # 1. Get or create Doctor
        doctor = db.query(models.ReferringDoctor).filter_by(name=dr_name).first()
        if not doctor:
            doctor = models.ReferringDoctor(name=dr_name)
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
            
        # 2. Get or create Patient
        patient = db.query(models.Patient).filter_by(name=patient_name).first()
        if not patient:
            patient = models.Patient(
                name=patient_name,
                dentrix_id=dentrix_id,
                referring_doctor_id=doctor.id
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
        # 3. Add Production record
        production = models.Production(
            patient_id=patient.id,
            amount=amount,
            month_year=month_year,
            date_recorded=date_obj
        )
        db.add(production)
        db.commit()
        records_added += 1
        
    return {"message": f"Successfully processed {records_added} records from CSV."}
