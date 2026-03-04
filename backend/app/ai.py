import json
import os

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are a helpful project management assistant for a Kanban board app.

The user's current board state is provided below as JSON. You can help the user by answering questions about their board, or by making changes to it.

When you want to modify the board, include a "board_updates" object in your response. Available actions:

- cards_to_create: array of {column_title, title, details} -- create new cards in the named column
- cards_to_update: array of {card_id, title?, details?} -- update existing cards (provide only fields to change)
- cards_to_delete: array of {card_id} -- delete cards by ID
- cards_to_move: array of {card_id, column_title, position} -- move cards to a column at a position (0-indexed)

Column titles and card IDs come from the board state below. Card IDs look like "card-1", "card-2", etc.

IMPORTANT RULES:
- Your entire response must be a single flat JSON object with "message" at the top level. Do NOT nest it inside another key.
- The "message" field is required and should be a natural language response to the user.
- The "board_updates" field is optional. Only include it if you are making changes.
- When creating cards, use the column's title (e.g. "Backlog", "In Progress"), not its ID.
- When moving cards, use the column's title.
- You can perform multiple operations at once.

Example response with no board changes:
{"message": "You have 5 columns."}

Example response with board changes:
{"message": "Done! I created the card.", "board_updates": {"cards_to_create": [{"column_title": "Backlog", "title": "My card", "details": "Some details"}]}}

Current board state:
"""


def get_ai_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def ai_test() -> str:
    """Send a simple test prompt and return the AI response text."""
    client = get_ai_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "What is 2+2? Reply with just the number."}],
    )
    return response.choices[0].message.content or ""


def ai_chat(board_json: dict, message: str, history: list[dict]) -> dict:
    """Send a chat message with board context and return parsed structured response."""
    client = get_ai_client()

    system_content = SYSTEM_PROMPT + json.dumps(board_json, indent=2)

    messages = [{"role": "system", "content": system_content}]
    for entry in history:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    return parse_ai_response(raw)


def parse_ai_response(raw: str) -> dict:
    """Parse the AI response JSON, handling malformed output gracefully."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"message": raw, "board_updates": None}

    if not isinstance(data, dict):
        return {"message": str(data), "board_updates": None}

    # Some models wrap the response in an extra key (e.g. {"final": {...}}).
    # Unwrap if "message" is missing but there's a single nested dict that has it.
    if "message" not in data:
        for v in data.values():
            if isinstance(v, dict) and "message" in v:
                data = v
                break

    if "message" not in data:
        # Empty or unrecognized response
        if not data:
            return {"message": "I couldn't process that request. Please try again.", "board_updates": None}
        return {"message": str(data), "board_updates": None}

    result: dict = {"message": data["message"]}

    updates = data.get("board_updates")
    if isinstance(updates, dict):
        clean: dict = {}
        for key in ("cards_to_create", "cards_to_update", "cards_to_delete", "cards_to_move"):
            if key in updates and isinstance(updates[key], list) and len(updates[key]) > 0:
                clean[key] = updates[key]
        result["board_updates"] = clean if clean else None
    else:
        result["board_updates"] = None

    return result
