import json
import os

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-oss-120b"

# Maximum number of cards to include in AI context to avoid token limits
MAX_CARDS_FOR_AI = 100

SYSTEM_PROMPT = """You are a helpful project management assistant for a Kanban board app.

The user's current board state is provided below as JSON. You can help the user by answering questions about their board, or by making changes to it.

When you want to modify the board, include a "board_updates" object in your response. Available actions:

- cards_to_create: array of {column_title, title, details, due_date?} -- create new cards in the named column. due_date is optional, format "YYYY-MM-DD".
- cards_to_update: array of {card_id, title?, details?, due_date?} -- update existing cards (provide only fields to change). Set due_date to null to clear it, or "YYYY-MM-DD" to set it.
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
{"message": "Done! I created the card.", "board_updates": {"cards_to_create": [{"column_title": "Backlog", "title": "My card", "details": "Some details", "due_date": "2026-04-01"}]}}

Example updating a due date:
{"message": "Updated the due date.", "board_updates": {"cards_to_update": [{"card_id": "card-1", "due_date": "2026-05-15"}]}}

Current board state:
"""


def get_ai_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def ai_test() -> str:
    client = get_ai_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "What is 2+2? Reply with just the number."}],
    )
    return response.choices[0].message.content or ""


def _truncate_board_for_ai(board_json: dict) -> tuple[dict, bool]:
    cards = board_json.get("cards", {})
    if len(cards) <= MAX_CARDS_FOR_AI:
        return board_json, False

    truncated_cards = dict(list(cards.items())[:MAX_CARDS_FOR_AI])
    kept_ids = set(truncated_cards.keys())

    truncated_columns = [
        {**col, "cardIds": [cid for cid in col.get("cardIds", []) if cid in kept_ids]}
        for col in board_json.get("columns", [])
    ]

    return {"columns": truncated_columns, "cards": truncated_cards}, True


def ai_chat(board_json: dict, message: str, history: list[dict]) -> dict:
    client = get_ai_client()

    board_for_ai, was_truncated = _truncate_board_for_ai(board_json)
    board_str = json.dumps(board_for_ai, indent=2)
    if was_truncated:
        board_str += f"\n\n(Note: Board truncated to {MAX_CARDS_FOR_AI} cards for context limit)"

    system_content = SYSTEM_PROMPT + board_str
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
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"message": raw, "board_updates": None}

    if not isinstance(data, dict):
        return {"message": str(data), "board_updates": None}

    # Some models wrap the response in an extra key (e.g. {"final": {...}}).
    if "message" not in data:
        for v in data.values():
            if isinstance(v, dict) and "message" in v:
                data = v
                break

    if "message" not in data:
        fallback = "I couldn't process that request. Please try again." if not data else str(data)
        return {"message": fallback, "board_updates": None}

    update_keys = ("cards_to_create", "cards_to_update", "cards_to_delete", "cards_to_move")
    updates = data.get("board_updates")
    board_updates = None
    if isinstance(updates, dict):
        clean = {k: updates[k] for k in update_keys if isinstance(updates.get(k), list) and updates[k]}
        board_updates = clean or None

    return {"message": data["message"], "board_updates": board_updates}
