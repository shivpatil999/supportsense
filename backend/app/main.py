import uuid
import boto3
import os
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Config ---
APP_NAME = os.getenv("APP_NAME", "SupportSense")
ENV = os.getenv("ENV", "development")
VERSION = os.getenv("VERSION", "0.1.3")


# --- DynamoDB ---
TABLE_NAME = os.getenv("DDB_TABLE")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

if not TABLE_NAME:
    raise RuntimeError("DDB_TABLE environment variable is not set")

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

class TicketStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]

# --- Routes ---
@app.get("/health")
def health():
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
    now = datetime.now(timezone.utc).isoformat()
    ticket_id = str(uuid.uuid4())

    item = {
        "ticket_id": ticket_id,
        "title": ticket.title,
        "description": ticket.description,
        "status": "open",
        "created_at": now,
        "updated_at": now,
    }

    try:
        table.put_item(Item=item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Ticket created successfully",
        "ticket": item,
    }

@app.patch("/tickets/{ticket_id}")
def update_ticket_status(ticket_id: str, update: TicketStatusUpdate):
    now = datetime.now(timezone.utc).isoformat()

    try:
        response = table.update_item(
            Key={"ticket_id": ticket_id},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": update.status,
                ":u": now,
            },
            ReturnValues="ALL_NEW",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Ticket updated successfully",
        "ticket": response["Attributes"],
    }

@app.get("/tickets")
def list_tickets():
    response = table.scan()
    return {
        "count": len(response.get("Items", [])),
        "tickets": response.get("Items", []),
    }

