from pathlib import Path
import re
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "pulseiq_warehouse.duckdb"
OUT = ROOT / "data" / "powerbi"
OUT.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB), read_only=True)

try:
    names = con.execute("""
        SELECT view_name
        FROM duckdb_views()
        WHERE schema_name = 'main'
        ORDER BY view_name
    """).fetchall()

    views = [
        row[0] for row in names
        if re.match(r"^vw_m\d{2}_", row[0])
        and not row[0].endswith("_base")
    ]

    print(f"Metric views found: {len(views)}")

    exported = 0
    for name in views:
        df = con.execute(f'SELECT * FROM "{name}"').df()
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"EXPORTED: {name} | rows={len(df)}")
        exported += 1

    print(f"\nExported views: {exported}")
    print(f"CSV folder: {OUT}")

finally:
    con.close()
