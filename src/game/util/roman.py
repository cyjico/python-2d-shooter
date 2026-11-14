_NUMERALS = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


def to_roman(number: int):
    """E.g. 14 -> "XIV". Needs a positive number."""
    if number < 1:
        raise ValueError("roman numerals start at 1")

    parts: list[str] = []
    for value, numeral in _NUMERALS:
        count, number = divmod(number, value)
        parts.append(numeral * count)
    return "".join(parts)
