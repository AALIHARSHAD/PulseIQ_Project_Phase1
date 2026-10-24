import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

try:
    print("--- Metric dictionary ---")
    print(con.execute("""
        SELECT metric_id, metric_name, source_table, grain,
               formula, minimum_group_size
        FROM metric_dictionary
        ORDER BY metric_id
    """).df().to_string(index=False))

    print("\n--- Headcount monthly schema ---")
    print(con.execute("""
        DESCRIBE fact_headcount_monthly
    """).df().to_string(index=False))

    print("\n--- Date dimension schema ---")
    print(con.execute("""
        DESCRIBE dim_date
    """).df().to_string(index=False))
finally:
    con.close()
