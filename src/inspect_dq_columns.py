import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

tables = [
    "fact_payroll", "fact_ledger", "fact_attendance_monthly",
    "fact_invoice", "fact_expense", "fact_task", "fact_leave",
    "fact_attrition_risk", "dim_employee", "metric_dictionary"
]

try:
    for table in tables:
        print(f"\n--- {table} ---")
        print(con.execute(f'SELECT * FROM "{table}" LIMIT 2').df().to_string(index=False))
        print("Columns:", [
            row[0] for row in con.execute(
                f"SELECT * FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position"
            ).fetchall()
        ])
finally:
    con.close()
