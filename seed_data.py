import pandas as pd
import random
from datetime import datetime, timedelta
import os
from database import SessionLocal, engine
import models
import ingestion

# Create dummy CSV
doctors = ["Dr. Smith (General)", "Dr. Jones (Ortho)", "Dr. Clark (Pedo)", "Dr. Adams (Endo)"]
base_date = datetime(2025, 10, 1)

data = []
for i in range(300):
    dr = random.choice(doctors)
    
    # Simulate Date
    date_offset = random.randint(0, 180)
    record_date = base_date + timedelta(days=date_offset)
    
    # Dr. Clark is decreasing rapidly in the last 30 days
    if dr == "Dr. Clark (Pedo)" and date_offset > 150:
        continue 
    # Dr. Adams stopped completely
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
csv_path = "dummy_dentrix_report.csv"
df.to_csv(csv_path, index=False)
print("Created dummy_dentrix_report.csv")

# Initialize and ingest
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()
res = ingestion.process_csv_file(csv_path, db)
print("Ingestion Result:", res)

# Test analytics
import analytics
print("\n--- Top Referrers ---")
top = analytics.get_top_referrers(db)
for t in top:
    print(t)

print("\n--- Referral Trends ---")
trends = analytics.get_referral_trends(db)
for t in trends:
    print(t)
