# backend\utils\llm_inference.py
import json
import logging
from typing import Any, Dict

import requests

from config import settings

logger = logging.getLogger(__name__)

LLM_MODEL = "@cf/meta/llama-3.2-3b-instruct"
ALLOWED_INTENTS = {
    "schedule_appointment",
    "cancel_appointment",
    "check_appointment",
    "general_chat",
}


def _run_llm(messages: list[dict[str, str]]) -> dict[str, Any]:
    account_id = settings.cloudflare_account_id
    auth_token = settings.cloudflare_auth_token

    response = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{LLM_MODEL}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"messages": messages},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _extract_text_response(result: dict[str, Any]) -> str:
    llm_result = result.get("result", {})

    if isinstance(llm_result, dict):
        response_text = llm_result.get("response")
        if isinstance(response_text, str):
            return response_text.strip()

    return ""


def _parse_intent_response(raw_text: str) -> Dict[str, Any]:
    fallback = {
        "intent": "general_chat",
        "confidence": 0.0,
        "reason": "Failed to parse classifier response",
    }

    if not raw_text:
        return fallback

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Intent classifier returned non-JSON output: %s", raw_text)
        return fallback

    intent = parsed.get("intent", "general_chat")
    confidence = parsed.get("confidence", 0.0)
    reason = parsed.get("reason", "")

    if intent not in ALLOWED_INTENTS:
        logger.warning("Intent classifier returned unknown intent: %s", intent)
        intent = "general_chat"

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(0.0, min(confidence, 1.0))

    return {
        "intent": intent,
        "confidence": confidence,
        "reason": reason,
    }


async def detect_intent(message: str) -> Dict[str, Any]:
    classifier_prompt = f"""
Classify the user's message into exactly one of these intents:
- schedule_appointment
- cancel_appointment
- check_appointment
- general_chat

Return valid JSON only in this format:
{{"intent":"general_chat","confidence":0.0,"reason":"short explanation"}}

Classification rules:
- schedule_appointment: the user wants to book, schedule, reserve, or set up an appointment.
- cancel_appointment: the user wants to cancel, stop, remove, or delete an existing appointment.
- check_appointment: the user wants to check, view, confirm, verify, or ask about an existing appointment or appointment status.
- general_chat: anything else, including greetings, unrelated questions, and broad support chat.

User message:
{message}
""".strip()

    try:
        result = _run_llm(
            [
                {
                    "role": "system",
                    "content": (
                        "You are an intent classifier. "
                        "Return strict JSON with no markdown."
                    ),
                },
                {"role": "user", "content": classifier_prompt},
            ]
        )
    except requests.RequestException as exc:
        logger.error("Intent detection failed: %s", exc)
        return {
            "intent": "general_chat",
            "confidence": 0.0,
            "reason": "Classifier request failed",
        }

    return _parse_intent_response(_extract_text_response(result))


async def get_llm_reponse(prompt: str) -> dict[str, Any]:
    result = _run_llm(
        [
            {"role": "system", "content": "You are a friendly assistant"},
            {"role": "user", "content": prompt},
        ]
    )
    return result
