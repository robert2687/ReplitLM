import re


def clean_code_markers(text: str) -> str:
    """
    Remove common markdown code fences like ```python ... ``` and surrounding noise.
    """
    s = text.strip()
    # If wrapped in triple backticks (optionally with a language tag), unwrap it
    fence_match = re.match(r"^```[a-zA-Z0-9_+-]*\n(?P<body>.*?)(\n```)?\s*$", s, flags=re.DOTALL)
    if fence_match:
        s = fence_match.group("body").strip()

    # Strip stray backticks if they remain
    s = s.strip("`").strip()

    return s