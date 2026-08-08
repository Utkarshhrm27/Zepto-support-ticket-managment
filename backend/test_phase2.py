import os
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    # the startup event has fired, building the index
    idx = app.state.similarity_index
    res = idx.top_k("milk packet missing from my order", k=1)
    print("Top match ID:", res[0].id)
    print("Top match score:", res[0].score)
