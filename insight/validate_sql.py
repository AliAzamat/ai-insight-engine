import re

ALLOWED_TABLES = {"mart_revenue", "fct_orders"}   # the ONLY tables NL queries may touch
_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|merge|grant)\b", re.I)
_TABLE_REF = re.compile(r"\bfrom\s+([a-z_][a-z0-9_]*)", re.I)

def validate(sql: str) -> str:
    s = sql.strip().rstrip(";")
    # 1) Exactly one statement: a stray ';' could smuggle a second command.
    if ";" in s:
        raise ValueError("only a single statement is allowed")
    # 2) Must be a read-only SELECT, no write keywords anywhere.
    if not s.lower().lstrip().startswith("select") or _FORBIDDEN.search(s):
        raise ValueError("only read-only SELECT statements are allowed")
    # 3) Every table referenced must be on the allowlist — no surprise sources.
    for table in _TABLE_REF.findall(s):
        if table.lower() not in ALLOWED_TABLES:
            raise ValueError(f"table {table!r} is not allowed")
    # 4) Force a bounded result so a runaway query can't dump the warehouse.
    if "limit" not in s.lower():
        s += "\nLIMIT 1000"
    return s
