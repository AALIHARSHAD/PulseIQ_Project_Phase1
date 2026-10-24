from pathlib import Path
import duckdb

root = Path(__file__).resolve().parents[1]
con = duckdb.connect(str(root / "data" / "pulseiq_warehouse.duckdb"))

views = [
    "vw_m22_task_completion_rate",
    "vw_m23_on_time_delivery_rate",
    "vw_m24_velocity",
    "vw_m25_average_cycle_time",
]

try:
    for name in views:
        row = con.execute(
            "SELECT sql FROM duckdb_views() WHERE view_name = ?",
            [name]
        ).fetchone()

        if not row:
            raise RuntimeError(f"View not found: {name}")

        definition = row[0]
        inner = name + "_base"
        query = definition.split(" AS ", 1)[1]

        con.execute(f'CREATE OR REPLACE VIEW "{inner}" AS {query}')
        con.execute(f"""
            CREATE OR REPLACE VIEW "{name}" AS
            SELECT team_id,
                   sprint_id,
                   CASE WHEN task_count < 5 THEN NULL
                        ELSE metric_value END AS metric_value,
                   task_count,
                   CASE WHEN task_count < 5 THEN 'SUPPRESSED'
                        ELSE 'PUBLISHED' END AS privacy_status
            FROM "{inner}"
        """)

        print(f"Updated {name}")

    print("\nSuppression summary:")
    for name in views:
        print(f"\n{name}")
        print(con.execute(f"""
            SELECT privacy_status, COUNT(*) AS groups
            FROM "{name}"
            GROUP BY privacy_status
            ORDER BY privacy_status
        """).df().to_string(index=False))

finally:
    con.close()
