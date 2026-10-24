import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

rows = con.execute("""
    SELECT table_name
    FROM information_schema.views
    WHERE table_schema = 'main'
      AND table_name LIKE 'vw_m%'
    ORDER BY table_name
""").fetchall()

for row in rows:
    print(row[0])

print("TOTAL METRIC VIEWS:", len(rows))
con.close()
