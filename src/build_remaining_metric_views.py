from pathlib import Path
import duckdb

root = Path(__file__).resolve().parents[1]
db = root / "data" / "pulseiq_warehouse.duckdb"
sql_file = root / "sql" / "remaining_metric_views.sql"

views = {
"vw_m16_revenue": """
SELECT posting_period AS month,
       -SUM(signed_amount_debit_positive) AS metric_value
FROM fact_ledger
WHERE account_code BETWEEN 4001 AND 4004
GROUP BY posting_period
""",
"vw_m17_net_profit": """
SELECT posting_period AS month,
       -SUM(signed_amount_debit_positive) AS metric_value
FROM fact_ledger
WHERE (account_code BETWEEN 4001 AND 4999)
   OR (account_code BETWEEN 5001 AND 5999)
GROUP BY posting_period
""",
"vw_m18_operating_margin": """
WITH totals AS (
    SELECT posting_period AS month,
           SUM(CASE WHEN account_code BETWEEN 4001 AND 4004
                    THEN -signed_amount_debit_positive ELSE 0 END) AS revenue,
           SUM(CASE WHEN account_code BETWEEN 4001 AND 4999
                          OR account_code BETWEEN 5001 AND 5999
                    THEN -signed_amount_debit_positive ELSE 0 END) AS net_profit
    FROM fact_ledger
    GROUP BY posting_period
)
SELECT month,
       net_profit * 100.0 / NULLIF(revenue, 0) AS metric_value
FROM totals
""",
"vw_m19_payroll_pct_revenue": """
WITH payroll AS (
    SELECT STRFTIME(CAST(period_end_date AS DATE), '%Y-%m') AS month,
           SUM(employer_cost) AS payroll_cost
    FROM fact_payroll
    GROUP BY 1
),
revenue AS (
    SELECT posting_period AS month,
           -SUM(signed_amount_debit_positive) AS revenue
    FROM fact_ledger
    WHERE account_code BETWEEN 4001 AND 4004
    GROUP BY 1
)
SELECT p.month,
       p.payroll_cost * 100.0 / NULLIF(r.revenue, 0) AS metric_value
FROM payroll p
LEFT JOIN revenue r ON p.month = r.month
""",
"vw_m20_dso": """
WITH monthly_revenue AS (
    SELECT posting_period AS month,
           -SUM(signed_amount_debit_positive) AS revenue
    FROM fact_ledger
    WHERE account_code BETWEEN 4001 AND 4004
    GROUP BY posting_period
),
receivables AS (
    SELECT STRFTIME(CAST(due_date AS DATE), '%Y-%m') AS month,
           SUM(balance_due) AS closing_receivables
    FROM fact_invoice
    WHERE status NOT IN ('DRAFT', 'CANCELLED')
    GROUP BY 1
)
SELECT r.month,
       r.closing_receivables * 90.0 / NULLIF(v.revenue, 0) AS metric_value
FROM receivables r
LEFT JOIN monthly_revenue v ON r.month = v.month
""",
"vw_m21_overdue_receivables": """
SELECT client_id, due_date AS report_date,
       SUM(balance_due) AS metric_value
FROM fact_invoice
WHERE due_date < DATE '2026-10-24'
  AND status NOT IN ('DRAFT', 'CANCELLED')
GROUP BY client_id, due_date
""",
"vw_m26_anomaly_flag_rate": """
SELECT source_dataset,
       STRFTIME(CAST(period AS DATE), '%Y-%m') AS month,
       COUNT(*) FILTER (WHERE flagged = 'Y') * 1.0 /
       NULLIF(COUNT(*), 0) AS metric_value,
       COUNT(*) AS record_count
FROM fact_anomaly
GROUP BY 1, 2
""",
"vw_m28_forecast_error_mape": """
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
"""
}

con = duckdb.connect(str(db))
try:
    for name, query in views.items():
        try:
            con.execute(f'CREATE OR REPLACE VIEW "{name}" AS {query}')
            count = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            print(f"PASS | {name} | rows={count}")
        except Exception as exc:
            print(f"FAIL | {name} | {exc}")

    sql_file.write_text(
        "\n\n".join(
            f'CREATE OR REPLACE VIEW "{name}" AS\n{query.strip()};'
            for name, query in views.items()
        ),
        encoding="utf-8"
    )
    print(f"\nSQL saved: {sql_file}")
finally:
    con.close()
