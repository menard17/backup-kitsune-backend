def to_bool(item: str) -> bool:
    if not item:
        return False
    true_set = {"true", "1"}
    return item.lower() in true_set
