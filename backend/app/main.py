import os
import uuid
from datetime import datetime, timezone
from typing import List, Literal

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------------
APP_NAME = os.getenv("APP_NAME", "SupportSense")
ENV = os.getenv("ENV", "development")
VERSION = os.getenv("VERSION", "0.1.3")

TABLE_NAME = os.getenv("DDB_TABLE")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

if not TABLE_NAME:
    raise RuntimeError("DDB_TABLE environment variable is not set")

# ------------------------------------------------------------------------------
# AWS
# ------------------------------------------------------------------------------
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

# ------------------------------------------------------------------------------
# FastAPI
# ------------------------------------------------------------------------------
tags_metadata = [
    {"name": "Health", "description": "Service health and operational checks."},
    {"name": "Tickets", "description": "Create and manage support tickets."},
]

app = FastAPI(
    title="SupportSense API",
    description=(
        "SupportSense is a lightweight support-ticket backend built with FastAPI and DynamoDB, "
        "deployed on AWS ECS (Fargate) behind an Application Load Balancer.\n\n"
        "This project demonstrates production-ready API design, clean contracts, "
        "and AWS-native deployment patterns."
    ),
    version=VERSION,
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------
class TicketCreate(BaseModel):
    title: str = Field(..., example="Payment failed on checkout")
    description: str = Field(
        ..., example="Customer receives a 500 error after clicking Pay."
    )


class TicketStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"] = Field(
        ..., example="resolved"
    )


class Ticket(BaseModel):
    ticket_id: str = Field(..., example="c9a2f1b0-3b7f-4b6e-a2e5-12aa01c8cabc")
    title: str
    description: str
    status: str = Field(..., example="open")
    created_at: str
    updated_at: str


class TicketList(BaseModel):
    count: int
    tickets: List[Ticket]


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Health"],
    summary="Service health check",
)
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "env": ENV,
        "version": VERSION,
        "table": TABLE_NAME,
        "region": AWS_REGION,
    }


@app.post(
    "/tickets",
    tags=["Tickets"],
    summary="Create a new support ticket",
    response_model=Ticket,
    status_code=201,
)
def create_ticket(ticket: TicketCreate):
    now = utc_now_iso()
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
    except ClientError as e:
        raise HTTPException(status_code=500, detail=e.response["Error"]["Message"])

    return item


@app.get(
    "/tickets",
    tags=["Tickets"],
    summary="List all support tickets",
    response_model=TicketList,
)
def list_tickets():
    try:
        response = table.scan()
    except ClientError as e:
        raise HTTPException(status_code=500, detail=e.response["Error"]["Message"])

    items = response.get("Items", [])
    return {"count": len(items), "tickets": items}


@app.get(
    "/tickets/{ticket_id}",
    tags=["Tickets"],
    summary="Get a ticket by ID",
    response_model=Ticket,
)
def get_ticket(ticket_id: str):
    try:
        resp = table.get_item(Key={"ticket_id": ticket_id})
    except ClientError as e:
        raise HTTPException(status_code=500, detail=e.response["Error"]["Message"])

    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return item


@app.patch(
    "/tickets/{ticket_id}",
    tags=["Tickets"],
    summary="Update ticket status",
    response_model=Ticket,
)
def update_ticket_status(ticket_id: str, update: TicketStatusUpdate):
    now = utc_now_iso()

    try:
        response = table.update_item(
            Key={"ticket_id": ticket_id},
            UpdateExpression="SET #s = :s, updated_at = :u",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": update.status, ":u": now},
            ConditionExpression="attribute_exists(ticket_id)",
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=404, detail="Ticket not found")
        raise HTTPException(status_code=500, detail=e.response["Error"]["Message"])

    return response["Attributes"]
