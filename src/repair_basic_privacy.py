from pathlib import Path
import re
import duckdb

root = Path.cwd()
db = root / "data" / "pulseiq_warehouse.duckdb"
sql_file = root / "sql" / "metric_views.sql"

sql_text = sql_file.read_text(encoding="utf-8")

thresholds = {
    "vw_m01_headcount": 5,
    "vw_m02_hires": 5,
    "vw_m03_exits": 5,
    "vw_m04_monthly_attrition_rate": 10,
    "vw_m05_rolling_12m_attrition": 10,
    "vw_m06_voluntary_attrition_rate": 10,
}

con = duckdb.connect(str(db))

try:
    for view, threshold in thresholds.items():
        pattern = (
            r'CREATE\s+OR\s+REPLACE\s+VIEW\s+"?'
            + re.escape(view)
            + r'"?\s+AS\s+.*?;'
        )
        match = re.search(pattern, sql_text, flags=re.IGNORECASE | re.DOTALL)

        if not match:
            raise RuntimeError(f"Original SQL definition not found: {view}")

        base_sql = re.sub(
            r'^(CREATE\s+OR\s+REPLACE\s+VIEW\s+)"?'
            + re.escape(view)
            + r'"?',
            r'\g<1>"' + view + '_base"',
            match.group(0),
            count=1,
            flags=re.IGNORECASE,
        )

        con.execute(base_sql)

        con.execute(f'''
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
            FROM "{view}_base" v
            JOIN fact_headcount_monthly h
              ON v.month_start_date = h.month_start_date
             AND v.department_id = h.department_id
        ''')

        con.execute(f'SELECT * FROM "{view}" LIMIT 1').fetchall()
        print(f"FIXED: {view} (threshold={threshold})")

    print("\nTesting all M01-M06 views...")
    for view in thresholds:
        count = con.execute(f'SELECT COUNT(*) FROM "{view}"').fetchone()[0]
        print(f"PASS: {view} | rows={count}")

finally:
    con.close()
