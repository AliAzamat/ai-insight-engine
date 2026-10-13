# AI Insight Engine

**A FastAPI service that puts an LLM layer on top of a data warehouse: structured executive briefs from metrics, a revenue forecast with a stated basis, and plain-English questions turned into SQL that must pass a read-only, table-allowlisted validator before anyone runs it.**

Analysts get the same questions every week — "how did revenue do, and where is it heading?", "which region had the most paid orders?" This service answers them with an LLM while keeping the model on a short leash: outputs are schema-validated, generated SQL is checked twice before it can be executed, identical requests are served from cache, and calls are retried and metered.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| `POST` | `/brief` | `{metrics, series}` → a validated `Insight` (`headline`, `trend`, `confidence` 0–1) plus a next-quarter revenue forecast with a one-sentence basis. Identical inputs are cached by a stable hash. |
| `GET` | `/ask?q=…` | Question → SQL against two allowed marts. Returns the validated SQL (execution is left to a read-only role elsewhere); unsafe SQL is a `400`. |
| `GET` | `/health` | Liveness |

## Guardrails on generated SQL

The model only sees the schemas of `mart_revenue` and `fct_orders` and is told to emit a single `SELECT`. Two independent checks then apply:

1. **At generation** (`nl_query.py`): reject anything containing write or DDL keywords or not starting with `SELECT`.
2. **Before returning** (`validate_sql.py`): reject multiple statements, any write keyword (including `GRANT`), and any `FROM` table outside the allowlist; append `LIMIT 1000` if the query has no limit.

Checked directly against the validator:

```text
SELECT region, SUM(revenue) FROM mart_revenue GROUP BY region   → allowed, LIMIT 1000 appended
select 1; drop table x                                          → rejected: single statement only
DELETE FROM fct_orders                                          → rejected: read-only SELECT only
select * from users                                             → rejected: table 'users' not allowed
```

## Other building blocks

- **Structured outputs** — JSON mode plus Pydantic validation, so a malformed model reply fails loudly instead of flowing downstream.
- **Retries** (`resilient.py`) — exponential backoff with jitter on timeouts, rate limits, and API errors, with a 20-second client timeout.
- **Cost routing** (`cache.py`) — `pick_model` sends "forecast / why / explain / trend" questions to a larger model and everything else to a cheaper one.
- **Observability** (`metrics.py`) — Prometheus latency histogram and cost/cache counters per model, with one structured log line per call.

## Running

Requires Python 3.10+ and an `OPENAI_API_KEY`.

```bash
git clone https://github.com/AliAzamat/ai-insight-engine.git
cd ai-insight-engine
pip install fastapi uvicorn openai pydantic prometheus_client
export OPENAI_API_KEY=<your key>

uvicorn insight.api:app --reload
curl "localhost:8000/ask?q=which+region+had+the+most+paid+orders"
```

## Limitations

- **The table allowlist only inspects `FROM`.** A `JOIN` to a disallowed table passes (`select * from mart_revenue m join users u …` is accepted); the validator should also check `JOIN` targets, or use a real SQL parser.
- The forecast is produced by the LLM, not a statistical model.
- `with_retries`, `pick_model`, and the Prometheus metrics are implemented but not yet wired into the request path; the cache is in-process memory.
- No dependency file, tests, or SQL execution layer.
