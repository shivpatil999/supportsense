import os
import uuid

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Config ---
APP_NAME = os.getenv("APP_NAME", "SupportSense")
ENV = os.getenv("ENV", "development")
VERSION = os.getenv("VERSION", "0.1.0")
DDB_TABLE = os.getenv("DDB_TABLE")

if not DDB_TABLE:
    raise RuntimeError("Missing environment variable DDB_TABLE")

# --- DynamoDB ---
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DDB_TABLE)

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
    return {"app_name": APP_NAME, "env": ENV, "version": VERSION, "ddb_table": DDB_TABLE}

@app.post("/tickets")
def create_ticket(ticket: Ticket):
    ticket_id = str(uuid.uuid4())

    item = {
        "ticket_id": ticket_id,
        "title": ticket.title,
        "description": ticket.description,
        "status": "open",
    }

    table.put_item(Item=item)

    return {"message": "Ticket created successfully", "ticket": item}

@app.get("/tickets")
def list_tickets():
    response = table.scan()
    items = response.get("Items", [])
    return {"count": len(items), "tickets": items}

