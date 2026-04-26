import pandas as pd

from src.data.load_raw import load_raw_listings
from src.data.validate import validate_required_columns, validate_non_empty
from src.data.prepare_dataset import rename_columns,clean_boolean_features,filter_invalid_rows,drop_listing_duplicates,add_price_per_sqm
from src.paths import PROCESSED_DIR


def build_processed_dataset() -> pd.DataFrame:
    df = load_raw_listings()

    validate_non_empty(df)
    validate_required_columns(df)

    df = rename_columns(df)
    df = clean_boolean_features(df)
    df = filter_invalid_rows(df)
    df = drop_listing_duplicates(df)
    df = add_price_per_sqm(df)

    return df


if __name__ == "__main__":
    df = build_processed_dataset()
    output_path = PROCESSED_DIR / "listings_processed.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved processed dataset to: {output_path}")
    print(f"Final shape: {df.shape}")