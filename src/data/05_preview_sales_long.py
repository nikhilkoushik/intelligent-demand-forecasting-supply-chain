
from pathlib import Path
import pandas as pd

CSV_PATH = Path("data/raw/sales_train_validation.csv")

# Start with just 3 product-store series.
# This lets us confirm the transformation safely.
sales = pd.read_csv(CSV_PATH, nrows=3)

# These columns describe each product and its store.
id_columns = [
    "item_id",
    "dept_id",
    "cat_id",
    "store_id",
    "state_id",
]

# Identify columns containing daily sales.
day_columns = [
    col for col in sales.columns
    if col.startswith("d_")
]

# Reshape from wide format to long format.
sales_long = sales.melt(
    id_vars=id_columns,
    value_vars=day_columns,
    var_name="d",
    value_name="units_sold",
)

# Display only the first 12 rows.
print("\nFirst 12 transformed rows:")
print(sales_long.head(12).to_string(index=False))

print("\nProduct-store series:", len(sales))
print("Days per series:", len(day_columns))
print("Total daily records:", len(sales_long))

# Check that sales quantities are valid.
print("Missing sales:", sales_long["units_sold"].isna().sum())
print("Negative sales:", (sales_long["units_sold"] < 0).sum())
