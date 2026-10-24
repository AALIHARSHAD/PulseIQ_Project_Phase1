import duckdb
from pathlib import Path

db = Path("data/pulseiq_warehouse.duckdb")
con = duckdb.connect(str(db), read_only=True)

try:
    print("DQ Checks Catalog:")
    result = con.execute('SELECT * FROM dq_checks_catalog').df()
    print("Rows:", len(result))
    print("Columns:", result.columns.tolist())
    print(result.to_string(index=False))
finally:
    con.close()
