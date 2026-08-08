from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
import csv
import io
from datetime import datetime
from typing import List

from app.database import SessionLocal
from app.models import Ticket, ResolvedTicket, DecisionLog, Order
from app.schemas import TicketOut, TicketDetailOut, OverrideRequest, DecisionLogOut, PrecedentDetail, OrderOut, TicketCreate
from app.services.pipeline import process_ticket

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

VALID_ACTIONS = ["redelivery", "full_refund", "partial_refund", "coupon", "refund_reissue", "apology_no_action", "escalation"]

@router.post("", response_model=TicketOut)
def create_ticket(req: TicketCreate, db: Session = Depends(get_db)):
    # Check if order exists, if not create dummy
    order = db.query(Order).filter(Order.id == req.order_id).first()
    if not order:
        order = Order(
            id=req.order_id,
            items=5,
            value_inr=1000,
            delivery_time_min=30,
            delivery_status="delivered"
        )
        db.add(order)
    
    # Generate new ID
    last_ticket = db.query(Ticket).filter(Ticket.id.like("N-%")).order_by(Ticket.id.desc()).first()
    new_num = 1
    if last_ticket:
        try:
            new_num = int(last_ticket.id.split("-")[1]) + 1
        except:
            pass
    t_id = f"N-{new_num:03d}"
    
    ticket = Ticket(
        id=t_id,
        order_id=req.order_id,
        description=req.description,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.post("/process-all")
def process_all_tickets(request: Request, db: Session = Depends(get_db)):
    pending = db.query(Ticket).filter(Ticket.status == "pending").all()
    count = 0
    for t in pending:
        process_ticket(db, t, request)
        count += 1
    return {"processed": count}

@router.post("/upload")
async def upload_tickets(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8-sig")))
    count = 0
    
    for row in reader:
        ticket_id = str(row["ticket_id"])
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            ticket = Ticket(id=ticket_id)
            db.add(ticket)
        
        if not row.get("created_at"):
            ticket.created_at = datetime.utcnow()
        else:
            try:
                ticket.created_at = datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
            except ValueError:
                ticket.created_at = datetime.utcnow()
            
        ticket.order_id = str(row["order_id"])
        ticket.description = str(row["description"])
        
        if not ticket.status:
            ticket.status = "pending"
        count += 1
        
    db.commit()
    return {"uploaded": count}

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
    res = TicketDetailOut.model_validate({
        **t.__dict__,
        "order": order,
        "precedents": precedents
    })
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
