from pathlib import Path

path = Path("src/build_remaining_metric_views.py")
text = path.read_text(encoding="utf-8")

start = text.index('"vw_m28_forecast_error_mape": """')
end = text.index('"""', text.index('"""', start) + 3) + 3

replacement = '''"vw_m28_forecast_error_mape": """
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
SELECT department_id,
       month,
       forecast_value,
       actual,
       CASE
           WHEN actual IS NULL OR actual = 0 THEN NULL
           ELSE ABS(actual - forecast_value) / ABS(actual) * 100.0
       END AS mape_pct,
       CASE
           WHEN actual IS NULL THEN 'PENDING_NO_ACTUALS'
           WHEN actual = 0 THEN 'PENDING_ZERO_ACTUAL'
           ELSE 'CALCULATED'
       END AS metric_status
FROM matched
"""'''

path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
print("Updated M28 definition in", path)
