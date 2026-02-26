from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.rules import global_cfg, iter_rules
from app.dedupe import exact_fingerprint, is_near_duplicate
from app.fatigue import compute_user_is_noisy
from app.ai import ai_assist_score

def _to_dt(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.replace(tzinfo=None)
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None
    return None

def _expires_at_passed(event: Dict[str, Any]) -> bool:
    exp = _to_dt(event.get("expires_at"))
    if not exp:
        return False
    now = _to_dt(event.get("timestamp")) or datetime.utcnow()
    return exp < now

def decide(
    event: Dict[str, Any],
    recent_exact_fps: List[str],
    recent_messages: List[str],
    count_10_min: int,
    promo_count_10_min: int,
) -> Tuple[str, Optional[datetime], List[str], str, Optional[str], Dict[str, Any]]:
    cfg = global_cfg()
    cap = int(cfg.get("max_notifications_per_user_per_10_min", 12))
    promo_cap = int(cfg.get("promotional_quiet_mode_cap_per_10_min", 2))

    user_is_noisy = compute_user_is_noisy(count_10_min, cap)
    promotion_cap_exceeded = promo_count_10_min >= promo_cap

    user_id = event["user_id"]
    event_type = event["event_type"]
    channel = event["channel"]
    message = event["message"]
    dedupe_key = event.get("dedupe_key")

    fp = exact_fingerprint(user_id, event_type, channel, message, dedupe_key)
    fp_seen = fp in set(recent_exact_fps)

    near_dup, near_score = is_near_duplicate(message, recent_messages)

    priority_hint = (event.get("priority_hint") or "").lower().strip()
    allow_duplicate_bypass = priority_hint in {"urgent"} or event_type in {"system_event"}

    context = {
        "expires_at_passed": _expires_at_passed(event),
        "is_exact_duplicate": fp_seen,
        "is_near_duplicate": near_dup,
        "near_duplicate_score": near_score,
        "user_is_noisy": user_is_noisy,
        "promotion_cap_exceeded": promotion_cap_exceeded,
        "allow_duplicate_bypass": allow_duplicate_bypass,
    }

    chosen: Optional[str] = None
    chosen_reason: Optional[str] = None
    chosen_rule: Optional[str] = None
    delay_seconds: Optional[int] = None

    for r in iter_rules():
        when = r.get("when", {}) or {}

        if "expires_at_passed" in when and bool(when["expires_at_passed"]) != context["expires_at_passed"]:
            continue
        if "event_type_in" in when and event_type not in set(when["event_type_in"]):
            continue
        if "priority_hint_in" in when and (priority_hint not in set(when["priority_hint_in"])):
            continue
        if "user_is_noisy" in when and bool(when["user_is_noisy"]) != context["user_is_noisy"]:
            continue
        if "promotion_cap_exceeded" in when and bool(when["promotion_cap_exceeded"]) != context["promotion_cap_exceeded"]:
            continue
        if "allow_duplicate_bypass" in when and bool(when["allow_duplicate_bypass"]) != context["allow_duplicate_bypass"]:
            continue
        if "is_exact_duplicate" in when and bool(when["is_exact_duplicate"]) != context["is_exact_duplicate"]:
            continue
        if "is_near_duplicate" in when and bool(when["is_near_duplicate"]) != context["is_near_duplicate"]:
            continue

        chosen = r.get("action")
        chosen_reason = r.get("reason", "Rule matched")
        chosen_rule = r.get("name")
        delay_seconds = r.get("delay_seconds")
        break

    if chosen is None:
        chosen = cfg.get("default_action", "later")
        chosen_reason = "Default policy"
        chosen_rule = None

    if chosen == "later":
        base_delay = int(cfg.get("later_delay_seconds", 120))
        if delay_seconds is None:
            delay_seconds = base_delay

    now = _to_dt(event.get("timestamp")) or datetime.utcnow()

    send_at = None
    if chosen == "later":
        send_at = now + timedelta(seconds=int(delay_seconds or 120))

    reason_codes: List[str] = []
    if context["expires_at_passed"]:
        reason_codes.append("expired")
    if fp_seen:
        reason_codes.append("exact_duplicate")
    if near_dup:
        reason_codes.append("near_duplicate")
    if user_is_noisy:
        reason_codes.append("noisy_user")
    if promotion_cap_exceeded:
        reason_codes.append("promotion_cap_exceeded")

    if chosen == "now":
        reason_codes.append("send_now")
    if chosen == "later":
        reason_codes.append("defer")
    if chosen == "never":
        reason_codes.append("suppress")

    ai = ai_assist_score(event, timeout_ms=50)

    meta = {
        "dedupe": {
            "fingerprint": fp,
            "is_exact_duplicate": fp_seen,
            "is_near_duplicate": near_dup,
            "near_score": near_score,
            "allow_duplicate_bypass": allow_duplicate_bypass,
        },
        "fatigue": {
            "count_10_min": count_10_min,
            "cap_10_min": cap,
            "user_is_noisy": user_is_noisy,
            "promo_count_10_min": promo_count_10_min,
            "promo_cap_10_min": promo_cap,
            "promotion_cap_exceeded": promotion_cap_exceeded,
        },
        "ai": ai,
    }

    explanation = f"{chosen.upper()} because {chosen_reason}. Context: {meta}"
    return chosen, send_at, reason_codes, explanation, chosen_rule, meta