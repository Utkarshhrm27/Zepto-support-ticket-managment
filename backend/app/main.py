from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.models import ResolvedTicket, Order, Ticket
from app.services.ingest import run_ingest
from app.services.similarity import SimilarityIndex

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if empty, run ingest
        if db.query(ResolvedTicket).count() == 0:
            run_ingest(db)
        
        # Build Similarity Engine
        resolved_tickets = db.query(ResolvedTicket).all()
        app.state.similarity_index = SimilarityIndex(resolved_tickets)
    finally:
        db.close()
    yield
    # Shutdown
    pass

from app.routers import tickets, stats

app = FastAPI(lifespan=lifespan)

app.include_router(tickets.router)
app.include_router(stats.router)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Zepto Support Ticket Manager API"}

@app.get("/api/debug/counts")
def debug_counts(db: Session = Depends(get_db)):
    return {
        "resolved": db.query(ResolvedTicket).count(),
        "orders": db.query(Order).count(),
        "tickets": db.query(Ticket).count()
    }
