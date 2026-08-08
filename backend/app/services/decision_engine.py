from pydantic import BaseModel
from collections import Counter
from app.models import Ticket, Order
from app.services.similarity import PrecedentMatch

class Decision(BaseModel):
    status: str
    action: str | None
    confidence: float | None
    reason: str
    refund_amount: int | None = None

def apply_order_guardrails(action: str, order: Order) -> tuple[str|None, str]:
    if order.delivery_status == "cancelled" and action == "redelivery":
        return None, "order is cancelled — redelivery is not a valid action"
    return action, "ok"

def decide(ticket: Ticket, order: Order, precedents: list[PrecedentMatch],
           threshold: float, require_agreement: bool) -> Decision:
    if not precedents:
        return Decision(status="needs_human", action=None, confidence=0.0, reason="no precedents found")
        
    top = precedents[0]
    actions = [p.action for p in precedents]
    agreement = len(set(actions)) == 1
    majority_action, majority_count = Counter(actions).most_common(1)[0]

    candidate_action = top.action
    confidence = top.score
    
    if require_agreement and not agreement:
        return Decision(status="needs_human", action=majority_action,
                         confidence=confidence, reason="precedents disagree on action")

    if top.action == "escalation":
        return Decision(status="needs_human", action=None, confidence=confidence,
                         reason="top precedent was an escalation, not an auto-resolvable action")

    guarded_action, guard_note = apply_order_guardrails(candidate_action, order)
    if guarded_action is None:
        return Decision(status="needs_human", action=candidate_action, confidence=confidence,
                         reason=guard_note)
    candidate_action = guarded_action

    if confidence < threshold:
        return Decision(status="needs_human", action=candidate_action, confidence=confidence,
                         reason=f"top similarity {confidence:.2f} below threshold {threshold}")

    return Decision(status="auto_resolved", action=candidate_action, confidence=confidence,
                     reason=f"matched {top.id} ({confidence:.2f}) and top-3 agree on '{candidate_action}'")
