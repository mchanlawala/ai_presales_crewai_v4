"""
json_utils.py
-------------
Robust JSON extraction from LLM output.
Handles markdown fences, trailing text, partial matches.
"""
import json
import re


def parse_json(text: str, fallback: dict | list | None = None):
    """
    Try multiple strategies to extract a JSON object or list from *text*.
    Returns *fallback* (default: empty dict) if nothing works.
    """
    if not text:
        return fallback if fallback is not None else {}

    # 1. Strip markdown fences
    cleaned = text
    for pattern in (r"```json\s*\n?(.*?)```", r"```\s*\n?(.*?)```"):
        m = re.search(pattern, cleaned, re.DOTALL)
        if m:
            cleaned = m.group(1).strip()
            break

    # 2. Direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Find first {...} or [...]
    for pattern in (r"\{.*\}", r"\[.*\]"):
        m = re.search(pattern, cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

    # 4. Give up
    print(f"⚠️  Could not parse JSON from: {text[:300]!r}")
    return fallback if fallback is not None else {}
