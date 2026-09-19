import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

ALLOWED_ORIGIN = "https://dpg.ourlovelysystem.org"

# Start small (2026-09-19): just prompt submission and a read-only feed.
# No replies, no personalities/models yet - those are separate features.
PROMPT_MAX_LEN = 2000
PROMPT_RETENTION_DAYS = 90
FEED_LIMIT = 50

SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
}


def response(status, body):
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def validate_session_id(session_id):
    return isinstance(session_id, str) and bool(SESSION_ID_RE.match(session_id))


def handle_post_prompt(body):
    session_id = body.get("session_id")
    authenticated_user_id = body.get("authenticated_user_id")
    display_name = body.get("display_name") or None
    text = (body.get("text") or "").strip()

    if not validate_session_id(session_id):
        return response(400, {"error": "invalid session_id"})
    if not text or len(text) > PROMPT_MAX_LEN:
        return response(400, {"error": f"text is required and must be at most {PROMPT_MAX_LEN} characters"})

    now = datetime.now(timezone.utc)
    prompt_id = uuid.uuid4().hex
    created_at = now.isoformat()
    ttl_epoch = int((now + timedelta(days=PROMPT_RETENTION_DAYS)).timestamp())

    table.put_item(Item={
        "pk": "PROMPT",
        "sk": f"{created_at}#{prompt_id}",
        "prompt_id": prompt_id,
        "session_id": session_id,
        "display_name": display_name,
        "authenticated_user_id": authenticated_user_id,
        "text": text,
        "created_at": created_at,
        "ttl": ttl_epoch,
    })
    return response(201, {"prompt_id": prompt_id, "created_at": created_at})


def handle_get_prompts():
    resp = table.query(
        KeyConditionExpression=Key("pk").eq("PROMPT"),
        ScanIndexForward=False,
        Limit=FEED_LIMIT,
    )
    prompts = [
        {
            "prompt_id": i["prompt_id"],
            "text": i["text"],
            "display_name": i.get("display_name"),
            "authenticated_user_id": i.get("authenticated_user_id"),
            "created_at": i["created_at"],
        }
        for i in resp.get("Items", [])
    ]
    return response(200, {"prompts": prompts})


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    if method == "OPTIONS":
        return response(200, {})

    raw_path = event.get("rawPath", "")
    segments = [s for s in raw_path.split("/") if s]

    try:
        if segments == ["prompts"] and method == "GET":
            return handle_get_prompts()
        if segments == ["prompts"] and method == "POST":
            body = json.loads(event.get("body") or "{}")
            return handle_post_prompt(body)
    except Exception as e:  # noqa: BLE001
        logger.exception("handler error")
        return response(500, {"error": str(e)})

    return response(404, {"error": "not found"})
