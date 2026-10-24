import duckdb

con = duckdb.connect(
    "data/pulseiq_warehouse.duckdb",
    read_only=True
)

for name in [
    "vw_m22_task_completion_rate",
    "vw_m23_on_time_delivery_rate",
    "vw_m24_velocity",
    "vw_m25_average_cycle_time"
]:
    print(f"\n--- {name} ---")
    print(con.execute(f"SELECT * FROM {name} LIMIT 5").df().to_string(index=False))

con.close()
