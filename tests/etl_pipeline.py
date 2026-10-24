
from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "PulseIQ_master_dataset.xlsx"
CLEAN = ROOT / "data" / "clean"
REJECTED = ROOT / "data" / "rejected"
REPORTS = ROOT / "reports"

for folder in [CLEAN, REJECTED, REPORTS]:
    folder.mkdir(parents=True, exist_ok=True)

# Read source workbook
excel = pd.ExcelFile(SOURCE)
summary = []

for sheet in excel.sheet_names:
    df = pd.read_excel(SOURCE, sheet_name=sheet)

    # Keep original data unchanged; export each sheet as a CSV
    output_name = sheet.lower() + ".csv"

    # Initial extraction only; no unsupported cleaning assumptions
    df.to_csv(CLEAN / output_name, index=False)

    summary.append({
        "sheet": sheet,
        "source_rows": len(df),
        "columns": len(df.columns),
        "exported_rows": len(df),
        "rejected_rows": 0,
        "status": "EXTRACTED - validation pending"
    })

summary_df = pd.DataFrame(summary)
summary_df.to_csv(REPORTS / "etl_summary.csv", index=False)

with open(REPORTS / "etl_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("ETL extraction completed.")
print("Sheets extracted:", len(summary))
print("Rows extracted:", summary_df["source_rows"].sum())
print("Summary:", REPORTS / "etl_summary.csv")
print(summary_df[["sheet", "source_rows", "status"]].to_string(index=False))
