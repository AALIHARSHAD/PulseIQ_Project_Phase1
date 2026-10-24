
import pandas as pd

file_path = "data/raw/PulseIQ_master_dataset.xlsx"

df = pd.read_excel(
    file_path,
    sheet_name="data_contracts"
)

print("DATA CONTRACTS")
print("=" * 60)

print("Rows:", len(df))
print("Columns:", df.columns.tolist())

print("\nContract details:")
print(df.to_string(index=False))
