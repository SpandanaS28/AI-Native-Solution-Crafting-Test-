from __future__ import annotations

from typing import Dict, Any

def compute_user_is_noisy(count_10_min: int, cap_10_min: int) -> bool:
    return count_10_min >= cap_10_min

def fatigue_meta(count_10_min: int, cap_10_min: int, user_is_noisy: bool) -> Dict[str, Any]:
    return {
        "count_10_min": count_10_min,
        "cap_10_min": cap_10_min,
        "user_is_noisy": user_is_noisy,
    }