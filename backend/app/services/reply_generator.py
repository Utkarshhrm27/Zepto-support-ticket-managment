import google.generativeai as genai
from app.models import Ticket
from app.services.decision_engine import Decision
from app.services.similarity import PrecedentMatch
from app.config import settings

if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)

def generate_reply(ticket: Ticket, decision: Decision, precedents: list[PrecedentMatch]) -> str:
    prompt = f"""You are a support agent for a quick-commerce delivery company.
Customer ticket: "{ticket.description}"
Action taken: {decision.action}
{f"Refund amount: Rs {decision.refund_amount}" if decision.refund_amount else ""}
Write a short (2-4 sentence), warm, specific customer-facing reply confirming this resolution.
Do not mention internal ticket IDs, similarity scores, or "precedents"."""

    if not settings.GOOGLE_API_KEY:
        return _fallback_reply(decision)

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return _fallback_reply(decision)

def _fallback_reply(decision: Decision) -> str:
    if decision.action == "redelivery":
        return "We sincerely apologize for the inconvenience. We have arranged a redelivery for the missing/incorrect items."
    elif decision.action in ["full_refund", "partial_refund"]:
        return f"We apologize for the issue. A refund of Rs {decision.refund_amount} has been processed and should reflect soon."
    elif decision.action == "coupon":
        return "We're sorry for the poor experience. A coupon has been added to your account for your next order."
    return "Thank you for reaching out. We have logged your concern and our team is looking into it."

def generate_reasoning(decision: Decision, precedents: list[PrecedentMatch]) -> str:
    # Templated, NOT an LLM call
    if not precedents:
        return f"No precedents matched. Decision: {decision.reason}"
    lines = [f"{p.id} ({p.category}, {p.score:.0%} match) -> {p.action}" for p in precedents]
    return f"Matched against: " + "; ".join(lines) + f". Decision: {decision.reason}"
