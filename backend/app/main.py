from fastapi import FastAPI
from pydantic import BaseModel

class Ticket(BaseModel):
    title: str
    description: str

app = FastAPI()

tickets = []

@app.get("/health")
def health_check():
    return {"status": "ok"}

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

