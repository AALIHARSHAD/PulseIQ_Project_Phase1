import duckdb

con = duckdb.connect("data/pulseiq_warehouse.duckdb", read_only=True)

views = [
    "vw_m01_headcount", "vw_m02_hires", "vw_m03_exits",
    "vw_m04_monthly_attrition_rate", "vw_m05_rolling_12m_attrition",
    "vw_m06_voluntary_attrition_rate", "vw_m07_gross_pay",
    "vw_m08_net_pay", "vw_m09_employer_payroll_cost",
    "vw_m10_cost_per_head", "vw_m11_overtime_share",
    "vw_m12_variable_pay_share", "vw_m13_attendance_rate",
    "vw_m14_late_arrival_rate", "vw_m15_leave_without_pay_days",
    "vw_m16_revenue", "vw_m17_net_profit", "vw_m18_operating_margin",
    "vw_m19_payroll_pct_revenue", "vw_m20_dso",
    "vw_m21_overdue_receivables", "vw_m22_task_completion_rate",
    "vw_m23_on_time_delivery_rate", "vw_m24_velocity",
    "vw_m25_average_cycle_time", "vw_m26_anomaly_flag_rate",
    "vw_m27_high_risk_share", "vw_m28_forecast_error_mape"
]

for view in views:
    try:
        columns = con.execute(
            f"SELECT * FROM {view} LIMIT 0"
        ).description
        names = [c[0] for c in columns]
        print(f"{view}: {', '.join(names)}")
    except Exception as e:
        print(f"{view}: ERROR - {e}")

con.close()
