from __future__ import annotations

import hashlib
import re
from typing import Tuple, List
from rapidfuzz import fuzz

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text

def exact_fingerprint(user_id: str, event_type: str, channel: str, message: str, dedupe_key: str | None) -> str:
    base = f"{user_id}|{event_type}|{channel}|{normalize_text(message)}|{dedupe_key or ''}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def is_near_duplicate(message: str, recent_messages: List[str], threshold: int = 92) -> Tuple[bool, int]:
    n = normalize_text(message)
    best = 0
    for m in recent_messages:
        score = fuzz.token_set_ratio(n, normalize_text(m))
        if score > best:
            best = score
    return best >= threshold, best