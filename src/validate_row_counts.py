from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
source = pd.read_csv(root / "reports" / "etl_summary.csv")
warehouse = pd.read_csv(root / "reports" / "warehouse_summary.csv")

source["table_name"] = source["sheet"].str.lower()
check = source.merge(
    warehouse[["table_name", "row_count"]],
    on="table_name",
    how="left"
)
check["match"] = check["source_rows"] == check["row_count"]
check["difference"] = check["row_count"] - check["source_rows"]

print("Source vs Warehouse Row Count Validation")
print("Tables checked:", len(check))
print("Matching tables:", int(check["match"].sum()))
print("Mismatched tables:", int((~check["match"]).sum()))

if (~check["match"]).any():
    print("\nMismatches:")
    print(check.loc[~check["match"], [
        "table_name", "source_rows", "row_count", "difference"
    ]].to_string(index=False))
else:
    print("\nSUCCESS: All source and warehouse row counts match.")

check.to_csv(root / "reports" / "row_count_validation.csv", index=False)
print("\nReport saved: reports/row_count_validation.csv")
