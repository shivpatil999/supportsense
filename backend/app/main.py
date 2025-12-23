import uuid
import boto3
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Config ---
APP_NAME = os.getenv("APP_NAME", "SupportSense")
ENV = os.getenv("ENV", "development")

# Bump this default so we can confirm the new container is running
VERSION = os.getenv("VERSION", "0.1.1")

# --- DynamoDB ---
TABLE_NAME = os.getenv("DDB_TABLE")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

if not TABLE_NAME:
    raise RuntimeError("DDB_TABLE environment variable is not set")

# Make region explicit (avoids "wrong region" / default region issues)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

# --- App ---
app = FastAPI(title=APP_NAME, version=VERSION)

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
    # This helps us confirm the deployed container is actually updated
    return {
        "status": "ok",
        "app": APP_NAME,
        "env": ENV,
        "version": VERSION,
        "table": TABLE_NAME,
        "region": AWS_REGION,
    }

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


