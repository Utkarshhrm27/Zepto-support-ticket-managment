import csv
from sqlalchemy.orm import Session
from app.models import ResolvedTicket, Order, Ticket
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def load_resolved_tickets(session: Session):
    path = os.path.join(DATA_DIR, "resolved_tickets.csv")
    if not os.path.exists(path): return
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticket = session.get(ResolvedTicket, row["ticket_id"])
            if not ticket:
                ticket = ResolvedTicket(id=row["ticket_id"])
                session.add(ticket)
            ticket.category = row["category"]
            ticket.description = row["description"]
            ticket.resolution_action = row["resolution_action"]
            ticket.resolution_note = row["resolution_note"]
            ticket.time_to_resolve_min = float(row["time_to_resolve_min"]) if row["time_to_resolve_min"] else 0
            ticket.csat = int(row["csat"]) if row["csat"] else 0
    session.commit()

def load_orders(session: Session):
    path = os.path.join(DATA_DIR, "orders_context.csv")
    if not os.path.exists(path): return
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            order = session.get(Order, row["order_id"])
            if not order:
                order = Order(id=row["order_id"])
                session.add(order)
            order.items = int(row["items"]) if row["items"] else 0
            order.value_inr = float(row["value_inr"]) if row["value_inr"] else 0
            order.delivery_time_min = int(row["delivery_time_min"]) if row["delivery_time_min"] else 0
            order.delivery_status = row["delivery_status"]
    session.commit()

def load_new_tickets(session: Session):
    path = os.path.join(DATA_DIR, "new_tickets.csv")
    if not os.path.exists(path): return
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticket = session.get(Ticket, row["ticket_id"])
            if not ticket:
                ticket = Ticket(id=row["ticket_id"])
                session.add(ticket)
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
    session.commit()

def run_ingest(session: Session):
    load_resolved_tickets(session)
    load_orders(session)
    load_new_tickets(session)
