import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Ticket
from app.services.pipeline import process_ticket

# We need a dummy request to pass to process_ticket to get app.state
class DummyRequest:
    def __init__(self, app):
        self.app = app

def test_pipeline():
    with TestClient(app) as client:
        # the app state is initialized during startup in the context manager above
        db = SessionLocal()
        try:
            ticket = db.query(Ticket).filter(Ticket.status == "pending").first()
            if not ticket:
                print("No pending ticket found to process")
                return

            print(f"Processing ticket: {ticket.id} ({ticket.description})")
            req = DummyRequest(app)
            processed = process_ticket(db, ticket, req)
            print(f"Status: {processed.status}")
            print(f"Drafted Reply: {processed.drafted_reply}")
        finally:
            db.close()

if __name__ == "__main__":
    test_pipeline()
