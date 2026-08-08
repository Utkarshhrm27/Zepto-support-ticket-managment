from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any

class OrderOut(BaseModel):
    id: str
    items: int
    value_inr: int
    delivery_time_min: int
    delivery_status: str

    class Config:
        from_attributes = True

class PrecedentDetail(BaseModel):
    id: str
    category: str
    description: str
    resolution_action: str
    resolution_note: str
    time_to_resolve_min: int
    csat: int

    class Config:
        from_attributes = True

class TicketOut(BaseModel):
    id: str
    description: str
    status: str
    inferred_category: Optional[str] = None
    predicted_action: Optional[str] = None
    final_action: Optional[str] = None
    confidence: Optional[float] = None
    refund_amount_inr: Optional[int] = None
    order_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TicketDetailOut(TicketOut):
    precedents: List[PrecedentDetail] = []
    reasoning: Optional[str] = None
    drafted_reply: Optional[str] = None
    order: OrderOut

class OverrideRequest(BaseModel):
    action: str
    reason: str
    resolved_by: str = "human"

class DecisionLogOut(BaseModel):
    id: int
    ticket_id: str
    event_type: str
    action: Optional[str] = None
    confidence: Optional[float] = None
    precedent_ids: Optional[Any] = None
    detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
