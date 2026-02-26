from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Literal, List
from pydantic import BaseModel, Field

Channel = Literal["push", "email", "sms", "in_app"]
Decision = Literal["now", "later", "never"]

class NotificationEvent(BaseModel):
    user_id: str
    event_type: str
    message: str = Field(..., description="Message or title")
    source: Optional[str] = None
    priority_hint: Optional[str] = None
    timestamp: datetime
    channel: Channel
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dedupe_key: Optional[str] = None
    expires_at: Optional[datetime] = None

class DecisionResponse(BaseModel):
    decision: Decision
    send_at: Optional[datetime] = None
    reason_codes: List[str]
    explanation: str
    rule_hit: Optional[str] = None
    dedupe: Dict[str, Any] = Field(default_factory=dict)
    fatigue: Dict[str, Any] = Field(default_factory=dict)
    ai: Dict[str, Any] = Field(default_factory=dict)

class RuleReloadResponse(BaseModel):
    ok: bool
    version: Optional[int] = None
    message: str