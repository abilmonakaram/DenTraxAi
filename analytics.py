from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from datetime import datetime
from typing import Dict, Set
from dataclasses import dataclass, field

@dataclass
class DoctorStats:
    historical_amount: float = 0.0
    historical_count: int = 0
    current_amount: float = 0.0
    current_count: int = 0
    months: Set[str] = field(default_factory=set)

def get_top_referrers(db: Session, limit: int = 10, by_production: bool = True):
    if by_production:
        results = db.query(
            models.ReferringDoctor.name,
            func.sum(models.Production.amount).label("total_production")
        ).select_from(models.ReferringDoctor).join(models.Patient).join(models.Production).group_by(models.ReferringDoctor.id).order_by(func.sum(models.Production.amount).desc()).limit(limit).all()
        return [{"doctor": r[0], "total_production": float(r[1] or 0.0)} for r in results]
    else:
        results = db.query(
            models.ReferringDoctor.name,
            func.count(models.Patient.id).label("patient_count")
        ).select_from(models.ReferringDoctor).join(models.Patient).group_by(models.ReferringDoctor.id).order_by(func.count(models.Patient.id).desc()).limit(limit).all()
        return [{"doctor": r[0], "total_patients": int(r[1] or 0)} for r in results]

def get_referral_trends(db: Session):
    today = datetime.today()
    current_month_str = today.strftime("%Y-%m")
    
    productions = db.query(
        models.ReferringDoctor.name,
        models.Production.month_year,
        func.sum(models.Production.amount).label("total_production"),
        func.count(models.Production.id).label("referral_count")
    ).select_from(models.ReferringDoctor).join(models.Patient).join(models.Production).group_by(
        models.ReferringDoctor.id, models.Production.month_year
    ).all()
    
    doctor_stats: Dict[str, DoctorStats] = {}
    for dr, m_y, amount, count in productions:
        amt = float(amount or 0.0)
        cnt = int(count or 0)
        dr_str = str(dr)
        m_y_str = str(m_y)
        
        if dr_str not in doctor_stats:
            doctor_stats[dr_str] = DoctorStats()
            
        if m_y_str == current_month_str:
            doctor_stats[dr_str].current_amount += amt
            doctor_stats[dr_str].current_count += cnt
        else:
            doctor_stats[dr_str].historical_amount += amt
            doctor_stats[dr_str].historical_count += cnt
            doctor_stats[dr_str].months.add(m_y_str)
            
    trends = []
    for dr, stats in doctor_stats.items():
        num_hist_months = max(1, len(stats.months))
        avg_hist_amount = stats.historical_amount / num_hist_months
        avg_hist_count = stats.historical_count / num_hist_months
        
        if stats.historical_count > 0 and stats.current_count == 0:
            status = "Lost"
        elif stats.current_count < (avg_hist_count * 0.5):
            status = "Decreasing"
        elif stats.current_count >= avg_hist_count:
            status = "Stable/Growing"
        else:
            status = "Slight Decrease"
            
        trends.append({
            "doctor": dr,
            "historical_avg_referrals": float(f"{avg_hist_count:.1f}"),
            "historical_avg_production": float(f"{avg_hist_amount:.2f}"),
            "current_month_referrals": stats.current_count,
            "current_month_production": float(f"{stats.current_amount:.2f}"),
            "status": status
        })
        
    def sort_key(x):
        priority = {"Lost": 0, "Decreasing": 1, "Slight Decrease": 2, "Stable/Growing": 3}
        return (priority[x["status"]], -x["historical_avg_production"])
        
    trends.sort(key=sort_key)
    return trends
