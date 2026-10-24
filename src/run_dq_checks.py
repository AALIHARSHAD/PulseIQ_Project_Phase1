from pathlib import Path
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "pulseiq_warehouse.duckdb"
OUT = ROOT / "reports" / "dq_results.csv"

con = duckdb.connect(str(DB))
checks = []

def run_check(check_id, name, severity, sql, fix):
    try:
        df = con.execute(sql).df()
        checks.append({
            "check_id": check_id,
            "check_name": name,
            "severity": severity,
            "failed_rows": len(df),
            "status": "PASS" if len(df) == 0 else "FAIL",
            "sample_failures": df.head(5).to_json(orient="records", date_format="iso"),
            "fix_guidance": fix
        })
        print(f"{check_id} | {name} | failed rows: {len(df)}")
    except Exception as e:
        checks.append({
            "check_id": check_id,
            "check_name": name,
            "severity": severity,
            "failed_rows": None,
            "status": "ERROR",
            "sample_failures": str(e),
            "fix_guidance": fix
        })
        print(f"{check_id} | {name} | ERROR: {e}")

try:
    run_check("DQ-C02", "Ledger balanced", "Critical", """
        SELECT entry_id
        FROM fact_ledger
        GROUP BY entry_id
        HAVING ABS(SUM(debit) - SUM(credit)) > 0.005
    """, "Reject unbalanced entry and alert ledger owner")

    run_check("DQ-C03", "Unique payroll rows", "Critical", """
        SELECT employee_id, run_id
        FROM fact_payroll
        GROUP BY employee_id, run_id
        HAVING COUNT(*) > 1
    """, "Remove duplicates and trace source")

    run_check("DQ-C04", "No orphan payroll employees", "Critical", """
        SELECT DISTINCT f.employee_id
        FROM fact_payroll f
        LEFT JOIN dim_employee d ON f.employee_id = d.employee_id
        WHERE d.employee_id IS NULL
    """, "Fix employee key or load missing employee")

    run_check("DQ-C05", "No attendance after exit", "Warning", """
        SELECT a.attendance_fact_id, a.employee_id, a.period_end_date, d.exit_date
        FROM fact_attendance_monthly a
        JOIN dim_employee d
          ON a.employee_id = d.employee_id AND d.is_current = 'Y'
        WHERE d.exit_date IS NOT NULL
          AND CAST(a.period_end_date AS DATE) > LAST_DAY(CAST(d.exit_date AS DATE))
    """, "Ask HR to confirm exit date or remove invalid row")

    run_check("DQ-C06", "Unpaid leave deducted", "Warning", """
        SELECT a.employee_id, a.period_end_date, a.unpaid_absence_days, p.lop_days
        FROM fact_attendance_monthly a
        JOIN fact_payroll p
          ON a.employee_id = p.employee_id
         AND a.period_end_date = p.period_end_date
        WHERE a.unpaid_absence_days > 0
          AND p.lop_days < a.unpaid_absence_days - 0.5
    """, "Review unpaid-leave mapping")

    run_check("DQ-C07", "Invoice arithmetic", "Warning", """
        SELECT invoice_id, amount_paid, total_amount, balance_due
        FROM fact_invoice
        WHERE amount_paid > total_amount + 0.01 OR balance_due < -0.01
    """, "Correct payment record")

    run_check("DQ-C08", "Expense arithmetic", "Warning", """
        SELECT expense_id, total_amount, amount_excl_gst, gst_amount
        FROM fact_expense
        WHERE ABS(total_amount - (amount_excl_gst + gst_amount)) > 0.01
    """, "Correct bill entry")

    run_check("DQ-C09", "Task dates sensible", "Warning", """
        SELECT task_id, started_date, completed_date, status
        FROM fact_task
        WHERE (started_date IS NOT NULL AND completed_date IS NOT NULL
               AND CAST(completed_date AS DATE) < CAST(started_date AS DATE))
           OR (status = 'Done' AND completed_date IS NULL)
    """, "Ask team to fix task board data")

    run_check("DQ-C10", "Leave dates sensible", "Warning", """
        SELECT leave_request_id, start_date, end_date
        FROM fact_leave
        WHERE CAST(end_date AS DATE) < CAST(start_date AS DATE)
    """, "Fix swapped dates")

    run_check("DQ-C11", "AI feed freshness", "Warning", """
        SELECT prediction_id, as_of_date
        FROM fact_attrition_risk
        WHERE CAST(as_of_date AS DATE) <
              (SELECT MAX(CAST(as_of_date AS DATE)) FROM fact_attrition_risk) - INTERVAL 7 DAY
    """, "Ask AI team to rerun scoring")

    run_check("DQ-C12", "Dimension history overlap", "Critical", """
        SELECT a.employee_id, a.employee_key AS version_a, b.employee_key AS version_b,
               a.valid_from AS a_from, a.valid_to AS a_to,
               b.valid_from AS b_from, b.valid_to AS b_to
        FROM dim_employee a
        JOIN dim_employee b
          ON a.employee_id = b.employee_id
         AND a.employee_key < b.employee_key
         AND CAST(a.valid_to AS DATE) >= CAST(b.valid_from AS DATE)
    """, "Close earlier version before next version starts")

    run_check("DQ-C14", "Minimum group size metadata", "Critical", """
        SELECT metric_id, metric_name, minimum_group_size
        FROM metric_dictionary
        WHERE minimum_group_size IS NULL OR minimum_group_size < 5
    """, "Suppress small groups; verify metric privacy threshold")

    # C01 needs finance mapping to be verified before comparing amounts.
    # C13 requires an ETL run log which has not yet been implemented.
    checks.extend([
        {
            "check_id": "DQ-C01", "check_name": "Payroll equals ledger",
            "severity": "Critical", "failed_rows": None, "status": "PENDING",
            "sample_failures": "Needs verified account-code and monthly cost mapping.",
            "fix_guidance": "Verify salary expense accounts 5001-5005 and payroll employer cost."
        },
        {
            "check_id": "DQ-C13", "check_name": "Pipeline freshness",
            "severity": "Critical", "failed_rows": None, "status": "PENDING",
            "sample_failures": "etl_run_log not implemented yet.",
            "fix_guidance": "Create ETL run log with started_at, finished_at and status."
        }
    ])

    result = pd.DataFrame(checks)
    result.to_csv(OUT, index=False)
    print("\nDQ results saved:", OUT)
    print("\nStatus summary:")
    print(result.groupby("status").size().to_string())
finally:
    con.close()
