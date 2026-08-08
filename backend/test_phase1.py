import os
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    response = client.get("/api/debug/counts")
    print("STATUS_CODE:", response.status_code)
    print("JSON:", response.json())
