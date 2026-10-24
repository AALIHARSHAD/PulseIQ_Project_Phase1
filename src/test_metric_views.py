import duckdb
from pathlib import Path

db = Path("data/pulseiq_warehouse.duckdb")
con = duckdb.connect(str(db), read_only=True)

try:
    views = con.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_name LIKE 'vw_m%'
        ORDER BY table_name
    """).fetchall()

    passed = 0
    failed = 0

    for (view_name,) in views:
        try:
            count = con.execute(
                f'SELECT COUNT(*) FROM "{view_name}"'
            ).fetchone()[0]
            print(f"PASS | {view_name} | rows={count}")
            passed += 1
        except Exception as exc:
            print(f"FAIL | {view_name} | {exc}")
            failed += 1

    print(f"\nTotal views: {len(views)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
finally:
    con.close()
