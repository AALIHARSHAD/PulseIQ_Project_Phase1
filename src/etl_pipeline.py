from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "PulseIQ_master_dataset.xlsx"
CLEAN = ROOT / "data" / "clean"
REPORTS = ROOT / "reports"

CLEAN.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

if not SOURCE.exists():
    raise FileNotFoundError(f"Source file missing: {SOURCE}")

excel = pd.ExcelFile(SOURCE)
summary = []

for sheet in excel.sheet_names:
    df = pd.read_excel(SOURCE, sheet_name=sheet)
    df.to_csv(CLEAN / f"{sheet.lower()}.csv", index=False)

    summary.append({
        "sheet": sheet,
        "source_rows": len(df),
        "columns": len(df.columns),
        "exported_rows": len(df),
        "status": "EXTRACTED - validation pending"
    })

summary_df = pd.DataFrame(summary)
summary_df.to_csv(REPORTS / "etl_summary.csv", index=False)

with open(REPORTS / "etl_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("ETL extraction completed.")
print("Sheets extracted:", len(summary))
print("Total rows extracted:", summary_df["source_rows"].sum())
print("Summary:", REPORTS / "etl_summary.csv")
