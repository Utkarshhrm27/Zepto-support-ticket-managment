from app.models import Ticket, Order
from app.services.decision_engine import decide, Decision
from app.services.similarity import PrecedentMatch
from app.services.pricing import refund_amount
from datetime import datetime

def run_tests():
    # Scenario 1: Clear missing-item ticket with strong precedents -> auto_resolved, refund_amount <= order.value_inr
    ticket = Ticket(id="T1", description="missing item")
    order = Order(id="O1", value_inr=1000, delivery_status="delivered")
    precedents = [
        PrecedentMatch(id="H1", action="partial_refund", category="missing_item", score=0.9),
        PrecedentMatch(id="H2", action="partial_refund", category="missing_item", score=0.88),
        PrecedentMatch(id="H3", action="partial_refund", category="missing_item", score=0.85)
    ]
    d1 = decide(ticket, order, precedents, threshold=0.55, require_agreement=True)
    assert d1.status == "auto_resolved"
    assert d1.action == "partial_refund"
    refund = refund_amount(d1.action, order)
    assert refund <= order.value_inr
    print("Scenario 1 passed")

    # Scenario 2: Novel/low-similarity ticket -> needs_human
    precedents_low = [
        PrecedentMatch(id="H1", action="partial_refund", category="missing_item", score=0.4),
        PrecedentMatch(id="H2", action="partial_refund", category="missing_item", score=0.38),
        PrecedentMatch(id="H3", action="partial_refund", category="missing_item", score=0.35)
    ]
    d2 = decide(ticket, order, precedents_low, threshold=0.55, require_agreement=True)
    assert d2.status == "needs_human"
    print("Scenario 2 passed")

    # Scenario 3: Top-3 precedents with mixed actions -> needs_human
    precedents_mixed = [
        PrecedentMatch(id="H1", action="full_refund", category="missing_item", score=0.9),
        PrecedentMatch(id="H2", action="partial_refund", category="missing_item", score=0.88),
        PrecedentMatch(id="H3", action="coupon", category="missing_item", score=0.85)
    ]
    d3 = decide(ticket, order, precedents_mixed, threshold=0.55, require_agreement=True)
    assert d3.status == "needs_human"
    print("Scenario 3 passed")

    # Scenario 4: Ticket on cancelled order whose top precedent is redelivery -> never auto-resolves as redelivery
    order_cancelled = Order(id="O2", value_inr=1000, delivery_status="cancelled")
    precedents_redelivery = [
        PrecedentMatch(id="H1", action="redelivery", category="missing_item", score=0.9),
        PrecedentMatch(id="H2", action="redelivery", category="missing_item", score=0.88),
        PrecedentMatch(id="H3", action="redelivery", category="missing_item", score=0.85)
    ]
    d4 = decide(ticket, order_cancelled, precedents_redelivery, threshold=0.55, require_agreement=True)
    assert d4.status == "needs_human"
    print("Scenario 4 passed")

if __name__ == "__main__":
    run_tests()
    print("All Phase 3 tests passed.")
