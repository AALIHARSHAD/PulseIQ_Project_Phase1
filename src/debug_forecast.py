import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

try:
    print("--- Forecast metrics ---")
    print(con.execute("""
        SELECT metric, department_id, COUNT(*) AS rows,
               MIN(forecast_month) AS first_month,
               MAX(forecast_month) AS last_month
        FROM fact_forecast
        GROUP BY 1, 2
        ORDER BY 1, 2
    """).df().to_string(index=False))

    print("\n--- Actual headcount months ---")
    print(con.execute("""
        SELECT department_id, COUNT(*) AS rows,
               MIN(month_start_date) AS first_month,
               MAX(month_start_date) AS last_month
        FROM fact_headcount_monthly
        GROUP BY department_id
        ORDER BY department_id
    """).df().to_string(index=False))

    print("\n--- Forecast departments ---")
    print(con.execute("""
        SELECT DISTINCT department_id
        FROM fact_forecast
        WHERE metric = 'headcount_end'
        ORDER BY 1
    """).df().to_string(index=False))

finally:
    con.close()
