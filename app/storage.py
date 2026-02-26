from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

DB_NAME = "engine.db"

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            event_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            send_at TEXT,
            explanation TEXT NOT NULL,
            rule_hit TEXT,
            reason_codes_json TEXT NOT NULL,
            meta_json TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS fingerprints (
            user_id TEXT NOT NULL,
            fp TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS deferred_queue (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            send_at TEXT NOT NULL,
            event_json TEXT NOT NULL,
            reason TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()

def insert_audit(
    user_id: str,
    event: Dict[str, Any],
    decision: str,
    send_at: Optional[datetime],
    explanation: str,
    rule_hit: Optional[str],
    reason_codes: List[str],
    meta: Dict[str, Any],
) -> str:
    conn = _connect()
    cur = conn.cursor()
    audit_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO audit_logs
        (id, user_id, created_at, event_json, decision, send_at, explanation, rule_hit, reason_codes_json, meta_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            user_id,
            datetime.utcnow().isoformat(),
            json.dumps(event, default=str),
            decision,
            send_at.isoformat() if send_at else None,
            explanation,
            rule_hit,
            json.dumps(reason_codes),
            json.dumps(meta, default=str),
        ),
    )
    conn.commit()
    conn.close()
    return audit_id

def enqueue_deferred(user_id: str, send_at: datetime, event: Dict[str, Any], reason: str) -> str:
    conn = _connect()
    cur = conn.cursor()
    qid = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO deferred_queue (id, user_id, created_at, send_at, event_json, reason)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (qid, user_id, datetime.utcnow().isoformat(), send_at.isoformat(), json.dumps(event, default=str), reason),
    )
    conn.commit()
    conn.close()
    return qid

def fetch_audit_for_user(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM audit_logs
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def count_recent_for_user(user_id: str, minutes: int) -> int:
    since = datetime.utcnow() - timedelta(minutes=minutes)
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) as c FROM audit_logs
        WHERE user_id = ? AND created_at >= ?
        """,
        (user_id, since.isoformat()),
    )
    c = int(cur.fetchone()["c"])
    conn.close()
    return c

def count_recent_by_type(user_id: str, event_type: str, minutes: int) -> int:
    since = datetime.utcnow() - timedelta(minutes=minutes)
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) as c FROM audit_logs
        WHERE user_id = ? AND created_at >= ? AND event_json LIKE ?
        """,
        (user_id, since.isoformat(), f'%"event_type": "{event_type}"%'),
    )
    c = int(cur.fetchone()["c"])
    conn.close()
    return c

def add_fingerprint(user_id: str, fp: str) -> None:
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO fingerprints (user_id, fp, created_at) VALUES (?, ?, ?)",
        (user_id, fp, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

def get_recent_fingerprints(user_id: str, minutes: int) -> List[str]:
    since = datetime.utcnow() - timedelta(minutes=minutes)
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT fp FROM fingerprints
        WHERE user_id = ? AND created_at >= ?
        """,
        (user_id, since.isoformat()),
    )
    fps = [r["fp"] for r in cur.fetchall()]
    conn.close()
    return fps