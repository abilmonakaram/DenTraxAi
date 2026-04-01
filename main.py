from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import shutil
import os

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

@app.post("/api/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/upload-csv/")
async def upload_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
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

@app.get("/api/doctors/", response_model=list[schemas.ReferringDoctor])
def list_doctors(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    doctors = db.query(models.ReferringDoctor).all()
    return doctors

@app.get("/api/analytics/top-referrers")
def get_top_referrers(
    limit: int = 10, 
    by_production: bool = True, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    return analytics.get_top_referrers(db, limit, by_production)

@app.get("/api/analytics/trends")
def get_referral_trends(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    return analytics.get_referral_trends(db)

# Mount frontend
from fastapi.staticfiles import StaticFiles
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
