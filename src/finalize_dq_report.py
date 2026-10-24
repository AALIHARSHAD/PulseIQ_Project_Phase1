from pathlib import Path
import pandas as pd
import json

root = Path(__file__).resolve().parents[1]
path = root / "reports" / "dq_results.csv"
df = pd.read_csv(path, keep_default_na=False)

c01 = {
    "check_id": "DQ-C01",
    "check_name": "Payroll equals ledger",
    "severity": "Critical",
    "failed_rows": 5,
    "status": "FAIL",
    "sample_failures": json.dumps([
        {"month":"2025-05","difference":61813.15},
        {"month":"2025-12","difference":98327.42},
        {"month":"2026-02","difference":154811.89},
        {"month":"2026-04","difference":96015.00},
        {"month":"2026-06","difference":-18450.00}
    ]),
    "fix_guidance": "Reconcile monthly payroll employer cost with ledger accounts 5001-5005; investigate posting differences before changing source data."
}

c14 = {
    "check_id": "DQ-C14",
    "check_name": "Minimum group size metadata",
    "severity": "Critical",
    "failed_rows": 9,
    "status": "FAIL",
    "sample_failures": json.dumps([
        {"metric_id":"M16","metric_name":"Revenue","issue":"Missing minimum_group_size"},
        {"metric_id":"M17","metric_name":"Net profit","issue":"Missing minimum_group_size"},
        {"metric_id":"M18","metric_name":"Operating margin","issue":"Missing minimum_group_size"},
        {"metric_id":"M19","metric_name":"Payroll as % of revenue","issue":"Missing minimum_group_size"},
        {"metric_id":"M20","metric_name":"Days sales outstanding (DSO)","issue":"Missing minimum_group_size"},
        {"metric_id":"M21","metric_name":"Overdue receivables","issue":"Missing minimum_group_size"},
        {"metric_id":"M24","metric_name":"Velocity","issue":"Missing minimum_group_size"},
        {"metric_id":"M26","metric_name":"Anomaly flag rate","issue":"Missing minimum_group_size"},
        {"metric_id":"M28","metric_name":"Forecast error (MAPE)","issue":"Missing minimum_group_size"}
    ]),
    "fix_guidance": "Obtain approved privacy thresholds for these nine metrics. Do not assume a default threshold or expose small groups."
}

for item in [c01, c14]:
    mask = df["check_id"] == item["check_id"]
    for col, value in item.items():
        df.loc[mask, col] = value

df.to_csv(path, index=False)

print("Updated DQ report:", path)
print("\nStatus summary:")
print(df.groupby("status").size().to_string())
print("\nCheck count:", len(df))
print("\nC01 and C14 updated; source data was not changed.")
