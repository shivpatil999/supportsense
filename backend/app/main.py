import uuid
import boto3
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Config ---
APP_NAME = os.getenv("APP_NAME", "SupportSense")
ENV = os.getenv("ENV", "development")
VERSION = os.getenv("VERSION", "0.1.0")

# --- DynamoDB ---
TABLE_NAME = os.getenv("DDB_TABLE")

if not TABLE_NAME:
    raise RuntimeError("DDB_TABLE environment variable is not set")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# --- App ---
app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.post("/tickets")
def create_ticket(ticket: Ticket):
    ticket_id = str(uuid.uuid4())

    item = {
        "ticket_id": ticket_id,   # ✅ REQUIRED PARTITION KEY
        "title": ticket.title,
        "description": ticket.description,
        "status": "open",
    }

    try:
        table.put_item(Item=item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Ticket created successfully",
        "ticket": item,
    }

@app.get("/tickets")
def list_tickets():
    response = table.scan()
    return {
        "count": len(response.get("Items", [])),
        "tickets": response.get("Items", []),
    }

