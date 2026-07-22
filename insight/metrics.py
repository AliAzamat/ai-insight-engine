import time
import logging
from prometheus_client import Counter, Histogram

logger = logging.getLogger("insight")

# Track latency AND spend — an LLM call costs real money per token.
llm_latency = Histogram("llm_seconds", "OpenAI call latency", ["model"])
llm_cost = Counter("llm_cost_usd", "Cumulative OpenAI spend", ["model"])
cache_hits = Counter("insight_cache_hits", "Briefs served from cache")
cache_misses = Counter("insight_cache_misses", "Briefs that hit the API")

class timed_call:
    """Context manager: records latency + cost for one model call."""
    def __init__(self, model: str, cost_usd: float):
        self.model, self.cost_usd = model, cost_usd
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, *exc):
        elapsed = time.time() - self.start
        llm_latency.labels(model=self.model).observe(elapsed)
        llm_cost.labels(model=self.model).inc(self.cost_usd)
        # Structured log: one line per call, machine-parseable.
        logger.info("llm_call", extra={"model": self.model, "seconds": elapsed})
