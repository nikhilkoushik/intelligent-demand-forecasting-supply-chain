
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")

files = [
    "calendar.csv",
    "sell_prices.csv",
    "sales_train_validation.csv",
    "sales_train_evaluation.csv",
    "sample_submission.csv",
]

for filename in files:
    path = DATA_DIR / filename

    print("\n" + "=" * 65)
    print("FILE:", filename)
    print("=" * 65)

    # Read only five rows to save memory.
    df = pd.read_csv(path, nrows=5)

    print("\nShape of preview:", df.shape)
    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst three rows:")
    print(df.iloc[:3, :12].to_string(index=False))