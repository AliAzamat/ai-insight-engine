from insight.client import summarize, Insight
from openai import OpenAI

client = OpenAI()

# Forecasting: give the model the recent series and ask for a grounded number.
FORECAST_SYSTEM = (
    "You are a forecasting assistant. Given a time-ordered revenue series, "
    "project next quarter. Explain your basis in one sentence. "
    "Respond as JSON: {\"next_quarter_revenue\": number, \"basis\": string}."
)

def forecast_revenue(series: list[float]) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": FORECAST_SYSTEM},
            {"role": "user", "content": f"Quarterly revenue: {series}"},
        ],
    )
    import json
    return json.loads(resp.choices[0].message.content)

# Compose: one call gives the executive a headline AND a forward look.
def executive_brief(metrics: dict, series: list[float]) -> dict:
    insight: Insight = summarize(metrics)
    forecast = forecast_revenue(series)
    return {"summary": insight.model_dump(), "forecast": forecast}
