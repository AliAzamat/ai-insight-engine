import re
from openai import OpenAI

client = OpenAI()

# Ground the model: tell it ONLY the marts it may query and their columns.
SCHEMA = """
mart_revenue(region TEXT, customer_tier TEXT, revenue NUMBER, paid_orders INT)
fct_orders(order_id TEXT, customer_id TEXT, amount NUMBER, status TEXT, ordered_date DATE)
"""

SYSTEM = f"""You translate questions into a SINGLE read-only SQL SELECT.
Use ONLY these tables/columns:
{SCHEMA}
Rules: SELECT statements only. Never write INSERT/UPDATE/DELETE/DROP.
Return only SQL, no prose."""

# Defense in depth: even if the prompt is coaxed, this gate blocks writes.
_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|merge)\b", re.I)

def to_sql(question: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
        ],
    )
    sql = resp.choices[0].message.content.strip().strip("`")
    if _FORBIDDEN.search(sql) or not sql.lower().lstrip().startswith("select"):
        raise ValueError("Generated SQL failed the read-only safety check")
    return sql
