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
lambda_client = boto3.client("lambda", region_name="us-east-1")
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
FUNCTION_NAME = os.environ["FUNCTION_NAME"]

ALLOWED_ORIGIN = "https://dpg.ourlovelysystem.org"

PROMPT_MAX_LEN = 2000
PROMPT_RETENTION_DAYS = 90
FEED_LIMIT = 50

ANSWER_TEXT_MAX_LEN = 2000
ANSWER_MAX_TOKENS = 600
LOOKUP_SCAN_LIMIT = 500  # small-scale app; a real index can replace this later

PERSONALITY_NAME_MAX_LEN = 80
PERSONALITY_PROMPTS_MAX_LEN = 4000
PERSONALITY_LIMIT = 50

# Verified functional for this account 2026-09-19 by actually invoking each
# one via bedrock-runtime:Converse, not just checking Bedrock's listing -
# see docs/models.md for the full reference table (all candidates tested,
# including the ones that failed and why). Update both together if this is
# ever refreshed; "id" is what actually gets passed to Converse later,
# whether that's a bare model ID or a us.-prefixed cross-region profile ID.
MODELS = [
    {"id": "amazon.nova-pro-v1:0", "provider": "Amazon", "name": "Nova Pro"},
    {"id": "amazon.nova-lite-v1:0", "provider": "Amazon", "name": "Nova Lite"},
    {"id": "amazon.nova-micro-v1:0", "provider": "Amazon", "name": "Nova Micro"},
    {"id": "us.amazon.nova-2-lite-v1:0", "provider": "Amazon", "name": "Nova 2 Lite"},
    {"id": "us.anthropic.claude-haiku-4-5-20251001-v1:0", "provider": "Anthropic", "name": "Claude Haiku 4.5"},
    {"id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0", "provider": "Anthropic", "name": "Claude Sonnet 4.5"},
    {"id": "us.anthropic.claude-sonnet-4-6", "provider": "Anthropic", "name": "Claude Sonnet 4.6"},
    {"id": "us.anthropic.claude-sonnet-5", "provider": "Anthropic", "name": "Claude Sonnet 5"},
    {"id": "us.anthropic.claude-opus-4-5-20251101-v1:0", "provider": "Anthropic", "name": "Claude Opus 4.5"},
    {"id": "us.anthropic.claude-opus-4-6-v1", "provider": "Anthropic", "name": "Claude Opus 4.6"},
    {"id": "us.anthropic.claude-opus-4-7", "provider": "Anthropic", "name": "Claude Opus 4.7"},
    {"id": "us.anthropic.claude-opus-4-8", "provider": "Anthropic", "name": "Claude Opus 4.8"},
    {"id": "us.anthropic.claude-opus-5", "provider": "Anthropic", "name": "Claude Opus 5"},
    {"id": "deepseek.v3.2", "provider": "DeepSeek", "name": "DeepSeek V3.2"},
    {"id": "us.deepseek.r1-v1:0", "provider": "DeepSeek", "name": "DeepSeek-R1"},
    {"id": "google.gemma-3-4b-it", "provider": "Google", "name": "Gemma 3 4B IT"},
    {"id": "google.gemma-3-12b-it", "provider": "Google", "name": "Gemma 3 12B IT"},
    {"id": "google.gemma-3-27b-it", "provider": "Google", "name": "Gemma 3 27B PT"},
    {"id": "meta.llama3-8b-instruct-v1:0", "provider": "Meta", "name": "Llama 3 8B Instruct"},
    {"id": "meta.llama3-70b-instruct-v1:0", "provider": "Meta", "name": "Llama 3 70B Instruct"},
    {"id": "us.meta.llama3-1-8b-instruct-v1:0", "provider": "Meta", "name": "Llama 3.1 8B Instruct"},
    {"id": "us.meta.llama3-1-70b-instruct-v1:0", "provider": "Meta", "name": "Llama 3.1 70B Instruct"},
    {"id": "us.meta.llama3-3-70b-instruct-v1:0", "provider": "Meta", "name": "Llama 3.3 70B Instruct"},
    {"id": "us.meta.llama4-scout-17b-instruct-v1:0", "provider": "Meta", "name": "Llama 4 Scout 17B Instruct"},
    {"id": "us.meta.llama4-maverick-17b-instruct-v1:0", "provider": "Meta", "name": "Llama 4 Maverick 17B Instruct"},
    {"id": "minimax.minimax-m2", "provider": "MiniMax", "name": "MiniMax M2"},
    {"id": "minimax.minimax-m2.1", "provider": "MiniMax", "name": "MiniMax M2.1"},
    {"id": "minimax.minimax-m2.5", "provider": "MiniMax", "name": "MiniMax M2.5"},
    {"id": "mistral.mistral-7b-instruct-v0:2", "provider": "Mistral AI", "name": "Mistral 7B Instruct"},
    {"id": "mistral.mixtral-8x7b-instruct-v0:1", "provider": "Mistral AI", "name": "Mixtral 8x7B Instruct"},
    {"id": "mistral.mistral-small-2402-v1:0", "provider": "Mistral AI", "name": "Mistral Small (24.02)"},
    {"id": "mistral.mistral-large-2402-v1:0", "provider": "Mistral AI", "name": "Mistral Large (24.02)"},
    {"id": "mistral.ministral-3-3b-instruct", "provider": "Mistral AI", "name": "Ministral 3B"},
    {"id": "mistral.ministral-3-8b-instruct", "provider": "Mistral AI", "name": "Ministral 3 8B"},
    {"id": "mistral.ministral-3-14b-instruct", "provider": "Mistral AI", "name": "Ministral 14B 3.0"},
    {"id": "mistral.magistral-small-2509", "provider": "Mistral AI", "name": "Magistral Small 2509"},
    {"id": "mistral.devstral-2-123b", "provider": "Mistral AI", "name": "Devstral 2 123B"},
    {"id": "mistral.mistral-large-3-675b-instruct", "provider": "Mistral AI", "name": "Mistral Large 3"},
    {"id": "us.mistral.pixtral-large-2502-v1:0", "provider": "Mistral AI", "name": "Pixtral Large (25.02)"},
    {"id": "mistral.voxtral-mini-3b-2507", "provider": "Mistral AI", "name": "Voxtral Mini 3B 2507"},
    {"id": "mistral.voxtral-small-24b-2507", "provider": "Mistral AI", "name": "Voxtral Small 24B 2507"},
    {"id": "moonshotai.kimi-k2.5", "provider": "Moonshot AI", "name": "Kimi K2.5"},
    {"id": "moonshot.kimi-k2-thinking", "provider": "Moonshot AI", "name": "Kimi K2 Thinking"},
    {"id": "us.moonshotai.kimi-k3", "provider": "Moonshot AI", "name": "Kimi K3"},
    {"id": "nvidia.nemotron-nano-9b-v2", "provider": "NVIDIA", "name": "Nemotron Nano 9B v2"},
    {"id": "nvidia.nemotron-nano-12b-v2", "provider": "NVIDIA", "name": "Nemotron Nano 12B v2 VL BF16"},
    {"id": "nvidia.nemotron-nano-3-30b", "provider": "NVIDIA", "name": "Nemotron Nano 3 30B"},
    {"id": "nvidia.nemotron-super-3-120b", "provider": "NVIDIA", "name": "Nemotron 3 Super 120B A12B"},
    {"id": "openai.gpt-oss-20b-1:0", "provider": "OpenAI", "name": "gpt-oss-20b"},
    {"id": "openai.gpt-oss-120b-1:0", "provider": "OpenAI", "name": "gpt-oss-120b"},
    {"id": "openai.gpt-oss-safeguard-20b", "provider": "OpenAI", "name": "GPT OSS Safeguard 20B"},
    {"id": "openai.gpt-oss-safeguard-120b", "provider": "OpenAI", "name": "GPT OSS Safeguard 120B"},
    {"id": "us.openai.gpt-5.6-terra", "provider": "OpenAI", "name": "GPT-5.6 Terra"},
    {"id": "us.openai.gpt-5.6-luna", "provider": "OpenAI", "name": "GPT-5.6 Luna"},
    {"id": "us.openai.gpt-5.6-sol", "provider": "OpenAI", "name": "GPT-5.6 Sol"},
    {"id": "us.openai.gpt-6-astra", "provider": "OpenAI", "name": "GPT-6 Astra"},
    {"id": "qwen.qwen3-32b-v1:0", "provider": "Qwen", "name": "Qwen3 32B (dense)"},
    {"id": "qwen.qwen3-coder-next", "provider": "Qwen", "name": "Qwen3 Coder Next"},
    {"id": "qwen.qwen3-coder-30b-a3b-v1:0", "provider": "Qwen", "name": "Qwen3-Coder-30B-A3B-Instruct"},
    {"id": "qwen.qwen3-next-80b-a3b", "provider": "Qwen", "name": "Qwen3 Next 80B A3B"},
    {"id": "qwen.qwen3-vl-235b-a22b", "provider": "Qwen", "name": "Qwen3 VL 235B A22B"},
    {"id": "writer.palmyra-vision-7b", "provider": "Writer", "name": "Palmyra Vision 7B"},
    {"id": "us.writer.palmyra-x4-v1:0", "provider": "Writer", "name": "Palmyra X4"},
    {"id": "us.writer.palmyra-x5-v1:0", "provider": "Writer", "name": "Palmyra X5"},
    {"id": "us.xai.grok-4.6", "provider": "xAI", "name": "Grok 4.6"},
    {"id": "zai.glm-4.7", "provider": "Z.AI", "name": "GLM 4.7"},
    {"id": "zai.glm-4.7-flash", "provider": "Z.AI", "name": "GLM 4.7 Flash"},
    {"id": "zai.glm-5", "provider": "Z.AI", "name": "GLM 5"},
]
MODEL_IDS = {m["id"] for m in MODELS}

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


def handle_get_models(event):
    # 2026-09-19: the models list (and, by extension, personality creation,
    # since a personality can't be created without picking one) requires
    # authentication. Matches this codebase's existing trust model elsewhere
    # (Touchstone's comment rate limits, etc.) - authenticated_user_id is
    # client-reported from the Cognito id_token, not re-verified server
    # side here, but its *absence* is what's actually enforced: no id, no
    # list.
    qs = event.get("queryStringParameters") or {}
    if not qs.get("authenticated_user_id"):
        return response(401, {"error": "sign in required to view models"})
    return response(200, {"models": MODELS})


def handle_post_personality(body):
    authenticated_user_id = body.get("authenticated_user_id")
    session_id = body.get("session_id")
    display_name = body.get("display_name") or None
    name = (body.get("name") or "").strip()
    prompts_text = (body.get("prompts") or "").strip()
    model_id = body.get("model_id")

    if not authenticated_user_id:
        return response(401, {"error": "sign in required to create a personality"})
    if not validate_session_id(session_id):
        return response(400, {"error": "invalid session_id"})
    if not name or len(name) > PERSONALITY_NAME_MAX_LEN:
        return response(400, {"error": f"name is required and must be at most {PERSONALITY_NAME_MAX_LEN} characters"})
    if not prompts_text or len(prompts_text) > PERSONALITY_PROMPTS_MAX_LEN:
        return response(400, {"error": f"prompts are required and must be at most {PERSONALITY_PROMPTS_MAX_LEN} characters"})
    if model_id not in MODEL_IDS:
        return response(400, {"error": "model_id must be one of the models returned by GET /models"})

    now = datetime.now(timezone.utc)
    personality_id = uuid.uuid4().hex
    created_at = now.isoformat()

    table.put_item(Item={
        "pk": "PERSONALITY",
        "sk": f"{created_at}#{personality_id}",
        "personality_id": personality_id,
        "session_id": session_id,
        "display_name": display_name,
        "authenticated_user_id": authenticated_user_id,
        "name": name,
        "prompts": prompts_text,
        "model_id": model_id,
        "created_at": created_at,
    })
    return response(201, {"personality_id": personality_id, "created_at": created_at})


def handle_get_personalities():
    # Read-only exposure is open to everyone, unlike creation - matches the
    # spec's "personality page... exposes the model and the read-only
    # prompts" being a public view, distinct from the auth-gated act of
    # constructing one.
    resp = table.query(
        KeyConditionExpression=Key("pk").eq("PERSONALITY"),
        ScanIndexForward=False,
        Limit=PERSONALITY_LIMIT,
    )
    personalities = [
        {
            "personality_id": i["personality_id"],
            "name": i["name"],
            "prompts": i["prompts"],
            "model_id": i["model_id"],
            "display_name": i.get("display_name"),
            "authenticated_user_id": i.get("authenticated_user_id"),
            "created_at": i["created_at"],
        }
        for i in resp.get("Items", [])
    ]
    return response(200, {"personalities": personalities})


def get_prompt_by_id(prompt_id):
    # No secondary index yet - fine at this scale (see LOOKUP_SCAN_LIMIT).
    resp = table.query(
        KeyConditionExpression=Key("pk").eq("PROMPT"),
        ScanIndexForward=False,
        Limit=LOOKUP_SCAN_LIMIT,
    )
    for i in resp.get("Items", []):
        if i["prompt_id"] == prompt_id:
            return i
    return None


def get_personality_by_id(personality_id):
    resp = table.query(
        KeyConditionExpression=Key("pk").eq("PERSONALITY"),
        ScanIndexForward=False,
        Limit=LOOKUP_SCAN_LIMIT,
    )
    for i in resp.get("Items", []):
        if i["personality_id"] == personality_id:
            return i
    return None


def handle_post_answer(body):
    prompt_id = body.get("prompt_id")
    session_id = body.get("session_id")
    authenticated_user_id = body.get("authenticated_user_id")
    display_name = body.get("display_name") or None
    mode = body.get("mode")

    if not validate_session_id(session_id):
        return response(400, {"error": "invalid session_id"})
    if not prompt_id or not get_prompt_by_id(prompt_id):
        return response(404, {"error": "prompt not found"})
    if mode not in ("self", "personality"):
        return response(400, {"error": "mode must be 'self' or 'personality'"})

    now = datetime.now(timezone.utc)
    answer_id = uuid.uuid4().hex
    created_at = now.isoformat()

    if mode == "self":
        text = (body.get("text") or "").strip()
        if not text or len(text) > ANSWER_TEXT_MAX_LEN:
            return response(400, {"error": f"text is required and must be at most {ANSWER_TEXT_MAX_LEN} characters"})
        table.put_item(Item={
            "pk": f"ANSWERS#{prompt_id}",
            "sk": f"{created_at}#{answer_id}",
            "answer_id": answer_id,
            "prompt_id": prompt_id,
            "author_type": "self",
            "session_id": session_id,
            "display_name": display_name,
            "authenticated_user_id": authenticated_user_id,
            "status": "complete",
            "text": text,
            "created_at": created_at,
        })
        return response(201, {"answer_id": answer_id, "status": "complete"})

    # mode == "personality"
    personality_id = body.get("personality_id")
    personality = personality_id and get_personality_by_id(personality_id)
    if not personality:
        return response(400, {"error": "personality not found"})

    table.put_item(Item={
        "pk": f"ANSWERS#{prompt_id}",
        "sk": f"{created_at}#{answer_id}",
        "answer_id": answer_id,
        "prompt_id": prompt_id,
        "author_type": "personality",
        "session_id": session_id,
        "display_name": display_name,
        "authenticated_user_id": authenticated_user_id,
        "personality_id": personality_id,
        "personality_name": personality["name"],
        "model_id": personality["model_id"],
        "status": "pending",
        "text": None,
        "created_at": created_at,
    })

    prompt_item = get_prompt_by_id(prompt_id)
    lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="Event",  # async - not behind API Gateway's timeout ceiling
        Payload=json.dumps({
            "internal_job": True,
            "prompt_id": prompt_id,
            "answer_id": answer_id,
            "created_at": created_at,
            "prompt_text": prompt_item["text"],
            "personality_prompts": personality["prompts"],
            "model_id": personality["model_id"],
        }),
    )
    return response(202, {"answer_id": answer_id, "status": "pending"})


def process_answer_job(event):
    key = {"pk": f"ANSWERS#{event['prompt_id']}", "sk": f"{event['created_at']}#{event['answer_id']}"}
    # attribute_exists guard: async invocations can in principle still be
    # retried (platform-level, outside MaximumRetryAttempts=0's control in
    # rare cases) or race a delete - without this, update_item's default
    # upsert behavior would silently recreate a bare, malformed item for an
    # answer that was already removed. Found this the hard way (2026-09-19):
    # a retried job outlived a deleted pending record and did exactly that.
    condition = "attribute_exists(pk)"
    try:
        resp = bedrock_runtime.converse(
            modelId=event["model_id"],
            system=[{"text": event["personality_prompts"]}],
            messages=[{"role": "user", "content": [{"text": event["prompt_text"]}]}],
            inferenceConfig={"maxTokens": ANSWER_MAX_TOKENS},
        )
        text = resp["output"]["message"]["content"][0]["text"]
        table.update_item(
            Key=key,
            UpdateExpression="SET #s = :s, #t = :t",
            ConditionExpression=condition,
            ExpressionAttributeNames={"#s": "status", "#t": "text"},
            ExpressionAttributeValues={":s": "complete", ":t": text},
        )
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        logger.info("answer %s no longer exists, dropping result", event["answer_id"])
    except Exception as e:  # noqa: BLE001
        logger.exception("answer job failed")
        try:
            table.update_item(
                Key=key,
                UpdateExpression="SET #s = :s, #t = :t",
                ConditionExpression=condition,
                ExpressionAttributeNames={"#s": "status", "#t": "text"},
                ExpressionAttributeValues={":s": "error", ":t": str(e)[:500]},
            )
        except table.meta.client.exceptions.ConditionalCheckFailedException:
            logger.info("answer %s no longer exists, dropping error", event["answer_id"])


def handle_get_answers(prompt_id):
    resp = table.query(
        KeyConditionExpression=Key("pk").eq(f"ANSWERS#{prompt_id}"),
    )
    answers = [
        {
            "answer_id": i.get("answer_id"),
            "author_type": i.get("author_type"),
            "display_name": i.get("display_name"),
            "authenticated_user_id": i.get("authenticated_user_id"),
            "personality_name": i.get("personality_name"),
            "model_id": i.get("model_id"),
            "status": i.get("status"),
            "text": i.get("text"),
            "created_at": i.get("created_at"),
        }
        for i in resp.get("Items", [])
        if i.get("answer_id")  # defensive: drop any malformed/orphaned rows
    ]
    return response(200, {"answers": answers})


def handler(event, context):
    if event.get("internal_job"):
        process_answer_job(event)
        return {}
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
        if segments == ["models"] and method == "GET":
            return handle_get_models(event)
        if segments == ["personalities"] and method == "GET":
            return handle_get_personalities()
        if segments == ["personalities"] and method == "POST":
            body = json.loads(event.get("body") or "{}")
            return handle_post_personality(body)
        if segments == ["answers"] and method == "POST":
            body = json.loads(event.get("body") or "{}")
            return handle_post_answer(body)
        if len(segments) == 2 and segments[0] == "answers" and method == "GET":
            return handle_get_answers(segments[1])
    except Exception as e:  # noqa: BLE001
        logger.exception("handler error")
        return response(500, {"error": str(e)})

    return response(404, {"error": "not found"})
