import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

try:
    tables = [
        "fact_ledger",
        "fact_invoice",
        "fact_anomaly",
        "fact_forecast",
        "fact_headcount_monthly",
        "dim_client"
    ]

    existing = {
        row[0] for row in con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
        """).fetchall()
    }

    for table in tables:
        print(f"\n--- {table} ---")
        if table not in existing:
            print("TABLE NOT FOUND")
            continue

        print(con.execute(f'DESCRIBE "{table}"').df().to_string(index=False))
        print("\nSample rows:")
        print(con.execute(f'SELECT * FROM "{table}" LIMIT 2').df().to_string(index=False))

finally:
    con.close()
