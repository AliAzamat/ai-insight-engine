import json
from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI()  # reads OPENAI_API_KEY from the environment

# The SHAPE we demand back from the model — not free-form prose.
class Insight(BaseModel):
    headline: str = Field(description="One-sentence executive takeaway")
    trend: str = Field(description="'up' | 'down' | 'flat'")
    confidence: float = Field(ge=0, le=1)

SYSTEM = (
    "You are a precise analytics assistant. Given metrics, return an insight. "
    "Respond ONLY with JSON matching the requested schema."
)

def summarize(metrics: dict) -> Insight:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},  # force valid JSON
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(metrics)},
        ],
    )
    raw = resp.choices[0].message.content
    # Validate the model's JSON against our schema before trusting it.
    return Insight.model_validate_json(raw)
