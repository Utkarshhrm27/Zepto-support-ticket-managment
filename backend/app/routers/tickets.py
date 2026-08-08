from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import SessionLocal
from app.models import Ticket, ResolvedTicket, DecisionLog, Order
from app.schemas import TicketOut, TicketDetailOut, OverrideRequest, DecisionLogOut, PrecedentDetail, OrderOut
from app.services.pipeline import process_ticket

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

VALID_ACTIONS = ["redelivery", "full_refund", "partial_refund", "coupon", "refund_reissue", "apology_no_action", "escalation"]

@router.post("/process-all")
def process_all_tickets(request: Request, db: Session = Depends(get_db)):
    pending = db.query(Ticket).filter(Ticket.status == "pending").all()
    count = 0
    for t in pending:
        process_ticket(db, t, request)
        count += 1
    return {"processed": count}

@router.post("/{id}/process", response_model=TicketOut)
def process_single_ticket(id: str, request: Request, db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if t.status != "pending":
        return t
    return process_ticket(db, t, request)

@router.get("", response_model=List[TicketOut])
def get_board_tickets(lane: str = "all", db: Session = Depends(get_db)):
    query = db.query(Ticket)
    if lane == "auto":
        query = query.filter(Ticket.status == "auto_resolved")
    elif lane == "human":
        query = query.filter(Ticket.status.in_(["needs_human", "approved", "overridden"]))
    return query.all()

@router.get("/{id}", response_model=TicketDetailOut)
def get_ticket_detail(id: str, db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    order = db.query(Order).filter(Order.id == t.order_id).first()
    
    precedents = []
    if t.precedent_ids:
        for pid in t.precedent_ids:
            pt = db.query(ResolvedTicket).filter(ResolvedTicket.id == pid).first()
            if pt:
                precedents.append(pt)
                
    # manual conversion to deal with dict mapping
    res = TicketDetailOut.model_validate(t)
    res.precedents = [PrecedentDetail.model_validate(p) for p in precedents]
    res.order = OrderOut.model_validate(order)
    return res

@router.post("/{id}/approve")
def approve_ticket(id: str, db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    t.final_action = t.predicted_action
    t.resolved_by = "human"
    t.resolved_at = datetime.utcnow()
    t.status = "approved"
    
    db.add(DecisionLog(
        ticket_id=t.id,
        event_type="approve",
        action=t.final_action,
        confidence=t.confidence,
        precedent_ids=t.precedent_ids,
        detail="Human approved predicted action"
    ))
    db.commit()
    return {"status": "approved"}

@router.post("/{id}/override")
def override_ticket(id: str, req: OverrideRequest, db: Session = Depends(get_db)):
    if req.action not in VALID_ACTIONS:
        raise HTTPException(status_code=422, detail="Invalid resolution action")
        
    t = db.query(Ticket).filter(Ticket.id == id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    t.final_action = req.action
    t.resolved_by = req.resolved_by
    t.resolved_at = datetime.utcnow()
    t.status = "overridden"
    t.override_reason = req.reason
    
    db.add(DecisionLog(
        ticket_id=t.id,
        event_type="override",
        action=t.final_action,
        confidence=t.confidence,
        precedent_ids=t.precedent_ids,
        detail=req.reason
    ))
    db.commit()
    return {"status": "overridden"}

@router.get("/{id}/log", response_model=List[DecisionLogOut])
def get_ticket_log(id: str, db: Session = Depends(get_db)):
    return db.query(DecisionLog).filter(DecisionLog.ticket_id == id).order_by(DecisionLog.created_at).all()
