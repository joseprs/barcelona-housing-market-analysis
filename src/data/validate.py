import pandas as pd


REQUIRED_COLUMNS = [
    "value",
    "surface",
]


def validate_required_columns(df: pd.DataFrame) -> None:
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")


def validate_non_empty(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("Input dataframe is empty")