import time
import random
from openai import OpenAI, APITimeoutError, RateLimitError, APIError

client = OpenAI(timeout=20.0)   # never hang forever on one call

# Wrap any LLM call: retry the TRANSIENT failures, give up on the rest.
RETRYABLE = (APITimeoutError, RateLimitError, APIError)

def with_retries(call, *, attempts: int = 4):
    for i in range(attempts):
        try:
            return call()
        except RETRYABLE as e:
            if i == attempts - 1:
                raise                       # exhausted the budget — surface it
            # Exponential backoff with JITTER so retries don't thundering-herd.
            delay = (2 ** i) + random.random()
            time.sleep(delay)
