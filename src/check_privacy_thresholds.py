import pandas as pd

df = pd.read_excel(
    "data/raw/PulseIQ_master_dataset.xlsx",
    sheet_name="metric_dictionary"
)

cols = ["metric_id", "metric_name", "minimum_group_size"]
print(df[cols].to_string(index=False))

print("\nMissing thresholds:")
print(df.loc[df["minimum_group_size"].isna(), ["metric_id", "metric_name"]].to_string(index=False))
