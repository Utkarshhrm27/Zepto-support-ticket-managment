from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import Request

from app.models import Ticket, Order, DecisionLog
from app.services.decision_engine import decide
from app.services.pricing import refund_amount
from app.services.reply_generator import generate_reasoning, generate_reply
from app.config import settings

def process_ticket(session: Session, ticket: Ticket, request: Request) -> Ticket:
    order = session.get(Order, ticket.order_id)
    if not order:
        raise ValueError(f"Order {ticket.order_id} not found for ticket {ticket.id}")

    # Similarity Index is attached to app.state
    index = request.app.state.similarity_index
    precedents = index.top_k(ticket.description, k=3)

    decision = decide(ticket, order, precedents, settings.AUTO_RESOLVE_CONFIDENCE_THRESHOLD,
                       settings.AGREEMENT_REQUIRED)

    if decision.action:
        decision.refund_amount = refund_amount(decision.action, order)
    
    reasoning = generate_reasoning(decision, precedents)
    reply = generate_reply(ticket, decision, precedents)

    ticket.status = decision.status
    ticket.predicted_action = decision.action
    ticket.confidence = decision.confidence
    ticket.refund_amount_inr = decision.refund_amount
    ticket.precedent_ids = [p.id for p in precedents]
    ticket.precedent_scores = [p.score for p in precedents]
    
    if precedents:
        ticket.inferred_category = precedents[0].category

    ticket.reasoning = reasoning
    ticket.drafted_reply = reply

    if decision.status == "auto_resolved":
        ticket.final_action = decision.action
        ticket.resolved_by = "system"
        ticket.resolved_at = datetime.utcnow()

    event_type = "auto_resolve" if decision.status == "auto_resolved" else "queue_human"
    
    session.add(DecisionLog(
        ticket_id=ticket.id,
        event_type=event_type,
        action=decision.action,
        confidence=decision.confidence,
        precedent_ids=ticket.precedent_ids,
        detail=decision.reason
    ))
    session.commit()
    return ticket
