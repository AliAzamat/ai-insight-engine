import json
import hashlib
from insight.service import executive_brief

# Identical inputs must not re-bill the API. Hash the request into a key.
_CACHE: dict[str, dict] = {}

def _key(metrics: dict, series: list[float]) -> str:
    # Stable hash: sort keys so {'a':1,'b':2} and {'b':2,'a':1} match.
    payload = json.dumps({"m": metrics, "s": series}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

def cached_brief(metrics: dict, series: list[float]) -> dict:
    k = _key(metrics, series)
    if k in _CACHE:
        return _CACHE[k]            # cache HIT — zero API cost
    result = executive_brief(metrics, series)
    _CACHE[k] = result
    return result

# Route by difficulty: cheap model for routine work, flagship only when needed.
def pick_model(question: str) -> str:
    hard = any(w in question.lower() for w in ("forecast", "why", "explain", "trend"))
    return "gpt-4o" if hard else "gpt-4o-mini"
