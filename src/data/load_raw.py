import pandas as pd
from src.paths import RAW_LISTINGS_DIR


def load_raw_listings() -> pd.DataFrame:
    csv_files = sorted(RAW_LISTINGS_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_LISTINGS_DIR}")

    dataframes = [pd.read_csv(file) for file in csv_files]
    df = pd.concat(dataframes, ignore_index=True)

    return df