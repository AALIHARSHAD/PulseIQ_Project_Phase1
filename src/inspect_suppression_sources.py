import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

checks = {
    "fact_headcount_monthly": "SELECT * FROM fact_headcount_monthly LIMIT 3",
    "vw_m01_headcount": "SELECT * FROM vw_m01_headcount LIMIT 3",
    "vw_m04_monthly_attrition_rate": "SELECT * FROM vw_m04_monthly_attrition_rate LIMIT 3",
    "vw_m07_gross_pay": "SELECT * FROM vw_m07_gross_pay LIMIT 3",
    "vw_m27_high_risk_share": "SELECT * FROM vw_m27_high_risk_share LIMIT 3"
}

for name, sql in checks.items():
    print(f"\n--- {name} ---")
    print(con.execute(sql).df().to_string(index=False))

con.close()
