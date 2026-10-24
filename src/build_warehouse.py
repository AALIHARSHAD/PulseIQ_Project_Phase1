from pathlib import Path
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
DB_PATH = ROOT / "data" / "pulseiq_warehouse.duckdb"
SUMMARY_PATH = ROOT / "reports" / "warehouse_summary.csv"

con = duckdb.connect(str(DB_PATH))
results = []

try:
    for csv_file in sorted(CLEAN.glob("*.csv")):
        table_name = csv_file.stem

        con.execute(
            f'CREATE OR REPLACE TABLE "{table_name}" AS '
            'SELECT * FROM read_csv_auto(?, header=true, sample_size=-1)',
            [str(csv_file)]
        )

        row_count = con.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]

        column_count = len(
            con.execute(f'SELECT * FROM "{table_name}" LIMIT 0').description
        )

        results.append({
            "table_name": table_name,
            "row_count": row_count,
            "column_count": column_count
        })

    summary = pd.DataFrame(results)
    summary.to_csv(SUMMARY_PATH, index=False)

    print("Warehouse build completed.")
    print("Database:", DB_PATH)
    print("Tables loaded:", len(results))
    print("Total rows loaded:", summary["row_count"].sum())
    print("Summary:", SUMMARY_PATH)
    print(summary.to_string(index=False))

finally:
    con.close()
