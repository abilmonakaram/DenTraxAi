from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import shutil
import os
import pandas as pd
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from a .env file if it exists

import models, database, ingestion, schemas, analytics, auth

# Create the database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Dentrix Referral Tracker API")

# Setup CORS for the frontend web app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
def read_root():
    return {"message": "Dentrix Referral Tracker API is running."}

@app.get("/health")
def health_check():
    return {"status": "ok"}



@app.post("/api/upload-csv/")
async def upload_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the CSV
        result = ingestion.process_csv_file(temp_file_path, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/api/load-demo-data")
def load_demo_data(db: Session = Depends(database.get_db)):
    # Clear existing data so we don't multiply records 
    db.query(models.Production).delete()
    db.query(models.Patient).delete()
    db.query(models.ReferringDoctor).delete()
    db.commit()

    doctors = ["Dr. Smith (General)", "Dr. Jones (Ortho)", "Dr. Clark (Pedo)", "Dr. Adams (Endo)"]
    base_date = datetime.now() - timedelta(days=180) 
    
    data = []
    for i in range(350):
        dr = random.choice(doctors)
        date_offset = random.randint(0, 180)
        record_date = base_date + timedelta(days=date_offset)
        
        # Simulate Dr. Clark dropping off recently
        if dr == "Dr. Clark (Pedo)" and date_offset > 150:
            continue
        # Simulate Dr. Adams stopping entirely a while ago
        if dr == "Dr. Adams (Endo)" and date_offset > 120:
            continue
            
        amount = round(random.uniform(200.0, 8000.0), 2)
        data.append({
            "Patient Name": f"Test Patient {i}",
            "Dentrix ID": f"D{1000+i}",
            "Referred By": dr,
            "Production Amount": f"${amount:,.2f}",
            "Date": record_date.strftime("%Y-%m-%d")
        })
    
    df = pd.DataFrame(data)
    csv_path = "temp_demo.csv"
    df.to_csv(csv_path, index=False)
    
    result = ingestion.process_csv_file(csv_path, db)
    if os.path.exists(csv_path):
        os.remove(csv_path)
    return {"message": "Demo data loaded successfully!", "details": result}

@app.get("/api/doctors/", response_model=list[schemas.ReferringDoctor])
def list_doctors(
    db: Session = Depends(database.get_db)
):
    doctors = db.query(models.ReferringDoctor).all()
    return doctors

@app.get("/api/analytics/top-referrers")
def get_top_referrers(
    limit: int = 10, 
    by_production: bool = True, 
    db: Session = Depends(database.get_db)
):
    return analytics.get_top_referrers(db, limit, by_production)

@app.get("/api/analytics/trends")
def get_referral_trends(
    db: Session = Depends(database.get_db)
):
    return analytics.get_referral_trends(db)

# Mount frontend
from fastapi.staticfiles import StaticFiles
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
