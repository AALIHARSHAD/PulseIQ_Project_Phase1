import pandas as pd

df = pd.read_excel(
    "data/raw/PulseIQ_master_dataset.xlsx",
    sheet_name="metric_dictionary"
)

print("Columns:", df.columns.tolist())

mask = df.astype(str).apply(
    lambda col: col.str.contains(r"\bM28\b", case=False, na=False)
).any(axis=1)

print(df.loc[mask].to_string(index=False))
