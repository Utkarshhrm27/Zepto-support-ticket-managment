import pandas as pd
from sqlalchemy.orm import Session
from app.models import ResolvedTicket, Order, Ticket
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def load_resolved_tickets(session: Session):
    path = os.path.join(DATA_DIR, "resolved_tickets.csv")
    if not os.path.exists(path): return
    df = pd.read_csv(path, encoding="utf-8-sig")
    for _, row in df.iterrows():
        ticket = session.get(ResolvedTicket, row["ticket_id"])
        if not ticket:
            ticket = ResolvedTicket(id=row["ticket_id"])
            session.add(ticket)
        ticket.category = row["category"]
        ticket.description = row["description"]
        ticket.resolution_action = row["resolution_action"]
        ticket.resolution_note = row["resolution_note"]
        ticket.time_to_resolve_min = row["time_to_resolve_min"]
        ticket.csat = row["csat"]
    session.commit()

def load_orders(session: Session):
    path = os.path.join(DATA_DIR, "orders_context.csv")
    if not os.path.exists(path): return
    df = pd.read_csv(path, encoding="utf-8-sig")
    for _, row in df.iterrows():
        order = session.get(Order, row["order_id"])
        if not order:
            order = Order(id=row["order_id"])
            session.add(order)
        order.items = row["items"]
        order.value_inr = row["value_inr"]
        order.delivery_time_min = row["delivery_time_min"]
        order.delivery_status = row["delivery_status"]
    session.commit()

def load_new_tickets(session: Session):
    path = os.path.join(DATA_DIR, "new_tickets.csv")
    if not os.path.exists(path): return
    df = pd.read_csv(path, encoding="utf-8-sig")
    for _, row in df.iterrows():
        ticket = session.get(Ticket, row["ticket_id"])
        if not ticket:
            ticket = Ticket(id=row["ticket_id"])
            session.add(ticket)
        ticket.created_at = pd.to_datetime(row["created_at"])
        ticket.order_id = row["order_id"]
        ticket.description = row["description"]
        if not ticket.status:
            ticket.status = "pending"
    session.commit()

def run_ingest(session: Session):
    load_resolved_tickets(session)
    load_orders(session)
    load_new_tickets(session)
