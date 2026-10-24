import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

queries = {
    "C03 Duplicate payroll": """
        SELECT employee_id, run_id, COUNT(*) AS row_count
        FROM fact_payroll GROUP BY employee_id, run_id
        HAVING COUNT(*) > 1
    """,
    "C04 Orphan employees": """
        SELECT DISTINCT f.employee_id
        FROM fact_payroll f
        LEFT JOIN dim_employee d ON f.employee_id = d.employee_id
        WHERE d.employee_id IS NULL
    """,
    "C07 Invoice arithmetic": """
        SELECT invoice_id, amount_paid, total_amount, balance_due
        FROM fact_invoice
        WHERE amount_paid > total_amount + 0.01 OR balance_due < -0.01
    """,
    "C08 Expense arithmetic": """
        SELECT expense_id, amount_excl_gst, gst_amount, total_amount
        FROM fact_expense
        WHERE ABS(total_amount - (amount_excl_gst + gst_amount)) > 0.01
    """,
    "C09 Task dates": """
        SELECT task_id, started_date, completed_date, status
        FROM fact_task
        WHERE (started_date IS NOT NULL AND completed_date IS NOT NULL
               AND CAST(completed_date AS DATE) < CAST(started_date AS DATE))
           OR (status = 'Done' AND completed_date IS NULL)
        LIMIT 30
    """,
    "C10 Leave dates": """
        SELECT leave_request_id, start_date, end_date
        FROM fact_leave
        WHERE CAST(end_date AS DATE) < CAST(start_date AS DATE)
    """,
    "C12 Employee history overlaps": """
        SELECT a.employee_id, a.employee_key AS key_a, b.employee_key AS key_b,
               a.valid_from AS from_a, a.valid_to AS to_a,
               b.valid_from AS from_b, b.valid_to AS to_b
        FROM dim_employee a
        JOIN dim_employee b
          ON a.employee_id = b.employee_id
         AND a.employee_key < b.employee_key
         AND CAST(a.valid_to AS DATE) >= CAST(b.valid_from AS DATE)
    """
}

try:
    for name, sql in queries.items():
        print(f"\n--- {name} ---")
        print(con.execute(sql).df().to_string(index=False))

    print("\n--- C14 minimum_group_size values ---")
    print(con.execute("""
        SELECT minimum_group_size, COUNT(*) AS metrics
        FROM metric_dictionary
        GROUP BY minimum_group_size
        ORDER BY minimum_group_size
    """).df().to_string(index=False))

    print("\n--- Ledger account mapping ---")
    print(con.execute("""
        SELECT account_code, COUNT(*) AS ledger_rows,
               ROUND(SUM(credit), 2) AS credits,
               ROUND(SUM(debit), 2) AS debits
        FROM fact_ledger
        GROUP BY account_code
        ORDER BY account_code
    """).df().to_string(index=False))
finally:
    con.close()
