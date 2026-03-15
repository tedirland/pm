def parse_id(prefixed_id: str) -> int:
    """Strip 'col-' or 'card-' prefix and return the integer ID."""
    parts = prefixed_id.split("-", 1)
    if len(parts) == 2 and parts[0] in ("col", "card"):
        return int(parts[1])
    return int(prefixed_id)
