import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

try:
    print("--- DQ-C01: Payroll vs ledger by month ---")
    sql = """
    WITH payroll AS (
        SELECT STRFTIME(CAST(period_end_date AS DATE), '%Y-%m') AS month,
               SUM(employer_cost) AS payroll_cost
        FROM fact_payroll
        GROUP BY 1
    ),
    ledger AS (
        SELECT posting_period AS month,
               SUM(debit - credit) AS ledger_expense
        FROM fact_ledger
        WHERE CAST(account_code AS VARCHAR) IN ('5001','5002','5003','5004','5005')
        GROUP BY 1
    )
    SELECT COALESCE(p.month, l.month) AS month,
           ROUND(COALESCE(p.payroll_cost, 0), 2) AS payroll_cost,
           ROUND(COALESCE(l.ledger_expense, 0), 2) AS ledger_expense,
           ROUND(COALESCE(p.payroll_cost, 0) - COALESCE(l.ledger_expense, 0), 2) AS difference
    FROM payroll p
    FULL OUTER JOIN ledger l ON p.month = l.month
    WHERE ABS(COALESCE(p.payroll_cost, 0) - COALESCE(l.ledger_expense, 0)) > 0.01
    ORDER BY month
    """
    mismatches = con.execute(sql).df()
    print("Mismatch months:", len(mismatches))
    print(mismatches.to_string(index=False) if len(mismatches) else "No mismatches found.")

    print("\n--- DQ-C14: Minimum group size values ---")
    c14 = con.execute("""
        SELECT metric_id, metric_name, minimum_group_size,
               TRY_CAST(REGEXP_EXTRACT(CAST(minimum_group_size AS VARCHAR), '[0-9]+') AS INTEGER)
                   AS parsed_group_size
        FROM metric_dictionary
        WHERE TRY_CAST(REGEXP_EXTRACT(CAST(minimum_group_size AS VARCHAR), '[0-9]+') AS INTEGER) IS NULL
           OR TRY_CAST(REGEXP_EXTRACT(CAST(minimum_group_size AS VARCHAR), '[0-9]+') AS INTEGER) < 5
    """).df()
    print("Metrics needing review:", len(c14))
    print(c14.to_string(index=False) if len(c14) else "All metrics have a parseable threshold of at least 5.")
finally:
    con.close()
