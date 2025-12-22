import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Config ---
APP_NAME = os.getenv("APP_NAME", "SupportSense")
ENV = os.getenv("ENV", "development")
VERSION = os.getenv("VERSION", "0.1.0")

# --- App ---
app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class Ticket(BaseModel):
    title: str
    description: str

# --- Routes ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/config")
def config():
    return {
        "app_name": APP_NAME,
        "env": ENV,
        "version": VERSION,
    }

tickets = []

@app.post("/tickets")
def create_ticket(ticket: Ticket):
    tickets.append(ticket)
    return {
        "message": "Ticket created successfully",
        "ticket": ticket
    }

@app.get("/tickets")
def list_tickets():
    return {
        "count": len(tickets),
        "tickets": tickets
    }

