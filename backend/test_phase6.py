import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def test_api():
    with TestClient(app) as client:
        # Process all tickets
        res1 = client.post("/api/tickets/process-all")
        print("process-all:", res1.status_code, res1.json())
        
        # Get board
        res2 = client.get("/api/tickets?lane=all")
        print("board tickets:", res2.status_code, len(res2.json()))
        
        # Get stats
        res3 = client.get("/api/stats")
        print("stats:", res3.status_code, res3.json())

if __name__ == "__main__":
    test_api()
