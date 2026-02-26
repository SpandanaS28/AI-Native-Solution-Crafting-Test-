from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import FastAPI
from app.models import NotificationEvent, DecisionResponse, RuleReloadResponse
from app.storage import (
    init_db,
    insert_audit,
    fetch_audit_for_user,
    add_fingerprint,
    get_recent_fingerprints,
    count_recent_for_user,
    count_recent_by_type,
    enqueue_deferred,
)
from app.rules import load_rules, get_rules
from app.decision import decide

app = FastAPI(title="Notification Prioritization Engine", version="1.0")

@app.on_event("startup")
def _startup() -> None:
    init_db()
    load_rules()

@app.get("/")
def home() -> Dict[str, Any]:
    return {
        "service": "Notification Prioritization Engine",
        "docs": "/docs",
        "health": "/v1/health",
    }

@app.get("/v1/health")
def health() -> Dict[str, Any]:
    r = get_rules()
    return {"ok": True, "rules_version": r.version, "time": datetime.utcnow().isoformat()}

@app.post("/v1/decide", response_model=DecisionResponse)
def decide_notification(event: NotificationEvent) -> DecisionResponse:
    e = event.model_dump()
    user_id = e["user_id"]

    recent_fps = get_recent_fingerprints(user_id, minutes=10)

    rows = fetch_audit_for_user(user_id, limit=50)
    recent_messages: List[str] = []
    for row in rows:
        try:
            import json
            ev = json.loads(row["event_json"])
            if ev.get("message"):
                recent_messages.append(str(ev["message"]))
        except Exception:
            continue

    count_10_min = count_recent_for_user(user_id, minutes=10)
    promo_count_10_min = count_recent_by_type(user_id, "promotion", minutes=10)

    decision, send_at, reason_codes, explanation, rule_hit, meta = decide(
        event=e,
        recent_exact_fps=recent_fps,
        recent_messages=recent_messages,
        count_10_min=count_10_min,
        promo_count_10_min=promo_count_10_min,
    )

    add_fingerprint(user_id, meta["dedupe"]["fingerprint"])

    if decision == "later" and send_at is not None:
        enqueue_deferred(user_id=user_id, send_at=send_at, event=e, reason=rule_hit or "default_defer")

    insert_audit(
        user_id=user_id,
        event=e,
        decision=decision,
        send_at=send_at,
        explanation=explanation,
        rule_hit=rule_hit,
        reason_codes=reason_codes,
        meta=meta,
    )

    return DecisionResponse(
        decision=decision,
        send_at=send_at,
        reason_codes=reason_codes,
        explanation=explanation,
        rule_hit=rule_hit,
        dedupe=meta.get("dedupe", {}),
        fatigue=meta.get("fatigue", {}),
        ai=meta.get("ai", {}),
    )

@app.post("/v1/rules/reload", response_model=RuleReloadResponse)
def reload_rules() -> RuleReloadResponse:
    r = load_rules()
    return RuleReloadResponse(ok=True, version=r.version, message="Rules reloaded")

@app.get("/v1/users/{user_id}/audit")
def get_user_audit(user_id: str, limit: int = 50) -> Dict[str, Any]:
    rows = fetch_audit_for_user(user_id, limit=limit)
    return {"user_id": user_id, "items": rows}