import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Ticket
from app.services.decision_engine import Decision
from app.services.reply_generator import generate_reply, generate_reasoning
from app.services.similarity import PrecedentMatch

def test_ai_layer():
    ticket = Ticket(id="T1", description="milk packet was completely torn and spilling")
    decision = Decision(status="auto_resolved", action="full_refund", confidence=0.88, reason="test", refund_amount=100)
    
    precedents = [
        PrecedentMatch(id="H1", action="full_refund", category="quality_issue", score=0.88)
    ]
    
    print("Testing Reasoning Generator...")
    reasoning = generate_reasoning(decision, precedents)
    print("Reasoning Output:\n", reasoning)
    
    print("\nTesting Reply Generator (Gemini)...")
    reply = generate_reply(ticket, decision, precedents)
    print("Reply Output:\n", reply)

if __name__ == "__main__":
    test_ai_layer()
