def final_price(cents: int, member: bool) -> int:
    if cents < 0:
        raise ValueError("cents must be non-negative")
    if member:
        return cents * 90 // 100
    return cents
