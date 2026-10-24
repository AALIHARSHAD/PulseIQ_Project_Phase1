from pathlib import Path
import duckdb

root = Path(__file__).resolve().parents[1]
db = root / "data" / "pulseiq_warehouse.duckdb"

con = duckdb.connect(str(db))
try:
    # M01-M06: headcount itself is the group-size proxy.
    thresholds = {
        "vw_m01_headcount": 5,
        "vw_m02_hires": 5,
        "vw_m03_exits": 5,
        "vw_m04_monthly_attrition_rate": 10,
        "vw_m05_rolling_12m_attrition": 10,
        "vw_m06_voluntary_attrition_rate": 10,
    }

    for view, threshold in thresholds.items():
        con.execute(f"""
            CREATE OR REPLACE VIEW "{view}" AS
            SELECT
                v.month_start_date,
                v.department_id,
                CASE
                    WHEN h.headcount_end < {threshold} THEN NULL
                    ELSE v.metric_value
                END AS metric_value,
                h.headcount_end AS group_size,
                CASE
                    WHEN h.headcount_end < {threshold} THEN 'SUPPRESSED'
                    ELSE 'PUBLISHED'
                END AS privacy_status
            FROM "{view}" v
            JOIN fact_headcount_monthly h
              ON v.month_start_date = h.month_start_date
             AND v.department_id = h.department_id
        """)
        print(f"Updated {view}: minimum group size {threshold}")

    # M07-M15 and M27 already expose employee_count; use it to create
    # privacy-safe wrapper views, preserving the original values separately.
    for n in range(7, 16):
        view = f"vw_m{n:02d}_" + {
            7: "gross_pay", 8: "net_pay", 9: "employer_payroll_cost",
            10: "cost_per_head", 11: "overtime_share",
            12: "variable_pay_share", 13: "attendance_rate",
            14: "late_arrival_rate", 15: "leave_without_pay_days"
        }[n]
        con.execute(f"""
            CREATE OR REPLACE VIEW "{view}" AS
            SELECT *,
                   CASE WHEN employee_count < 5 THEN NULL
                        ELSE metric_value END AS published_metric_value,
                   CASE WHEN employee_count < 5 THEN 'SUPPRESSED'
                        ELSE 'PUBLISHED' END AS privacy_status
            FROM (
                SELECT * FROM "{view}_source"
            )
        """) if False else None

    print("\nM01-M06 privacy suppression applied.")
    print("M07-M15 and M27 need safe view wrappers next; original metric_value retained for now.")
finally:
    con.close()
