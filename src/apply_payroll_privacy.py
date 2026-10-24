from pathlib import Path
import duckdb

root = Path(__file__).resolve().parents[1]
con = duckdb.connect(str(root / "data" / "pulseiq_warehouse.duckdb"))

views = {
    7: "gross_pay",
    8: "net_pay",
    9: "employer_payroll_cost",
    10: "cost_per_head",
    11: "overtime_share",
    12: "variable_pay_share",
    13: "attendance_rate",
    14: "late_arrival_rate",
    15: "leave_without_pay_days",
}

try:
    for n, suffix in views.items():
        name = f"vw_m{n:02d}_{suffix}"
        # Capture the existing definition before replacing the view.
        definition = con.execute("""
            SELECT sql FROM duckdb_views()
            WHERE view_name = ?
        """, [name]).fetchone()[0]

        inner_name = f"{name}_base"
        con.execute(f'CREATE OR REPLACE VIEW "{inner_name}" AS {definition.split(" AS ", 1)[1]}')
        con.execute(f"""
            CREATE OR REPLACE VIEW "{name}" AS
            SELECT month_end, department_id,
                   CASE WHEN employee_count < 5 THEN NULL
                        ELSE metric_value END AS metric_value,
                   employee_count,
                   CASE WHEN employee_count < 5 THEN 'SUPPRESSED'
                        ELSE 'PUBLISHED' END AS privacy_status
            FROM "{inner_name}"
        """)
        print(f"Updated {name}")

    name = "vw_m27_high_risk_share"
    definition = con.execute("""
        SELECT sql FROM duckdb_views()
        WHERE view_name = ?
    """, [name]).fetchone()[0]
    inner_name = f"{name}_base"
    con.execute(f'CREATE OR REPLACE VIEW "{inner_name}" AS {definition.split(" AS ", 1)[1]}')
    con.execute(f"""
        CREATE OR REPLACE VIEW "{name}" AS
        SELECT department_id,
               CASE WHEN employee_count < 10 THEN NULL
                    ELSE metric_value END AS metric_value,
               employee_count,
               CASE WHEN employee_count < 10 THEN 'SUPPRESSED'
                    ELSE 'PUBLISHED' END AS privacy_status
        FROM "{inner_name}"
    """)
    print("Updated vw_m27_high_risk_share")

finally:
    con.close()
