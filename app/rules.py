from __future__ import annotations

import yaml
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

RULES_FILE = "rules.yaml"

@dataclass
class LoadedRules:
    version: int
    raw: Dict[str, Any]

_loaded: Optional[LoadedRules] = None

def load_rules() -> LoadedRules:
    global _loaded
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    version = int(raw.get("version", 1))
    _loaded = LoadedRules(version=version, raw=raw)
    return _loaded

def get_rules() -> LoadedRules:
    global _loaded
    if _loaded is None:
        return load_rules()
    return _loaded

def global_cfg() -> Dict[str, Any]:
    return get_rules().raw.get("global", {}) or {}

def channel_cfg(channel: str) -> Dict[str, Any]:
    channels = get_rules().raw.get("channels", {}) or {}
    return channels.get(channel, {}) or {}

def iter_rules() -> List[Dict[str, Any]]:
    return (get_rules().raw.get("rules", []) or [])