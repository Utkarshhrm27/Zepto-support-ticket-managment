from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.database import SessionLocal
from app.models import Ticket

router = APIRouter(prefix="/api/stats", tags=["Stats"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Ticket).count()
    auto_resolved = db.query(Ticket).filter(Ticket.status == "auto_resolved").count()
    needs_human = db.query(Ticket).filter(Ticket.status.in_(["needs_human", "approved", "overridden"])).count()
    
    # Calculate avg confidence only for processed tickets
    avg_conf = db.query(func.avg(Ticket.confidence)).filter(Ticket.confidence.isnot(None)).scalar()
    
    auto_resolve_rate = (auto_resolved / total) * 100 if total > 0 else 0
    
    return {
        "total": total,
        "auto_resolved": auto_resolved,
        "needs_human": needs_human,
        "avg_confidence": float(avg_conf) if avg_conf else 0.0,
        "auto_resolve_rate": round(auto_resolve_rate, 2)
    }
