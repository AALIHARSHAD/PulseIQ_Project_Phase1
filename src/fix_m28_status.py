from pathlib import Path
import duckdb

root = Path(__file__).resolve().parents[1]
db = root / "data" / "pulseiq_warehouse.duckdb"

query = """
WITH forecasts AS (
    SELECT department_id,
           forecast_month AS month,
           forecast_value
    FROM fact_forecast
    WHERE metric = 'headcount_end'
      AND department_id <> 'ALL'
),
actuals AS (
    SELECT department_id,
           month_start_date AS month,
           headcount_end AS actual
    FROM fact_headcount_monthly
),
matched AS (
    SELECT f.department_id,
           f.month,
           f.forecast_value,
           a.actual
    FROM forecasts f
    LEFT JOIN actuals a
      ON f.department_id = a.department_id
     AND f.month = a.month
)
SELECT
    department_id,
    month,
    forecast_value,
    actual,
    CASE
        WHEN actual IS NULL THEN NULL
        WHEN actual = 0 THEN NULL
        ELSE ABS(actual - forecast_value) / ABS(actual) * 100.0
    END AS mape_pct,
    CASE
        WHEN actual IS NULL THEN 'PENDING_NO_ACTUALS'
        WHEN actual = 0 THEN 'PENDING_ZERO_ACTUAL'
        ELSE 'CALCULATED'
    END AS metric_status
FROM matched
"""

con = duckdb.connect(str(db))
try:
    con.execute(
        f'CREATE OR REPLACE VIEW "vw_m28_forecast_error_mape" AS {query}'
    )
    print(con.execute("""
        SELECT metric_status, COUNT(*) AS rows
        FROM vw_m28_forecast_error_mape
        GROUP BY metric_status
        ORDER BY metric_status
    """).df().to_string(index=False))

    print("\nSample rows:")
    print(con.execute("""
        SELECT *
        FROM vw_m28_forecast_error_mape
        ORDER BY month, department_id
        LIMIT 10
    """).df().to_string(index=False))
finally:
    con.close()
