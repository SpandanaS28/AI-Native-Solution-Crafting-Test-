from __future__ import annotations

import time
from typing import Any, Dict

def ai_assist_score(event: Dict[str, Any], timeout_ms: int = 50) -> Dict[str, Any]:
    """
    Safe AI hook.
    This simulates an external model call with a strict time budget.
    If it cannot finish quickly, return fallback output.
    """
    start = time.perf_counter()
    try:
        # Put your real AI call here later.
        # For now we return quickly with neutral output.
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > timeout_ms:
            return {"used": False, "reason": "timeout_fallback"}
        return {"used": False, "reason": "disabled_stub"}
    except Exception as e:
        return {"used": False, "reason": "error_fallback", "error": str(e)[:120]}