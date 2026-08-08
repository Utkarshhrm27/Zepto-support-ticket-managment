from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON
from datetime import datetime
from app.database import Base

class ResolvedTicket(Base):
    __tablename__ = "resolved_tickets"
    id = Column(String, primary_key=True)
    category = Column(String, index=True)
    description = Column(Text)
    resolution_action = Column(String)
    resolution_note = Column(Text)
    time_to_resolve_min = Column(Integer)
    csat = Column(Integer)

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    items = Column(Integer)
    value_inr = Column(Integer)
    delivery_time_min = Column(Integer)
    delivery_status = Column(String, index=True)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True)
    created_at = Column(DateTime)
    order_id = Column(String, ForeignKey("orders.id"))
    description = Column(Text)

    status = Column(String, default="pending")
    inferred_category = Column(String, nullable=True)
    predicted_action = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    refund_amount_inr = Column(Integer, nullable=True)
    precedent_ids = Column(JSON, nullable=True)
    precedent_scores = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)
    drafted_reply = Column(Text, nullable=True)
    final_action = Column(String, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    override_reason = Column(Text, nullable=True)

class DecisionLog(Base):
    __tablename__ = "decision_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), index=True)
    event_type = Column(String)
    action = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    precedent_ids = Column(JSON, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
