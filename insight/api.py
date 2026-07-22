from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from insight.cache import cached_brief
from insight.nl_query import to_sql
from insight.validate_sql import validate

app = FastAPI(title="Insight Engine")

class BriefRequest(BaseModel):
    metrics: dict
    series: list[float]

@app.post("/brief")
def brief(req: BriefRequest) -> dict:
    # FastAPI already validated the body against BriefRequest.
    return cached_brief(req.metrics, req.series)

@app.get("/ask")
def ask(q: str) -> dict:
    # Generate SQL, then run it through the deeper validator. Map failures
    # to a 400 so a bad/unsafe question is a client error, not a 500 crash.
    try:
        safe_sql = validate(to_sql(q))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Returns the SAFE SQL; a read-only role executes it elsewhere.
    return {"sql": safe_sql}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
