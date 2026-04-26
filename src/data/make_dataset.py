from src.data.load_raw import load_raw_listings
from src.data.prepare_dataset import prepare_listings_dataset
from src.paths import PROCESSED_DIR


def build_processed_dataset():
    raw_df = load_raw_listings()
    processed_df = prepare_listings_dataset(raw_df,apply_outlier_filter=True)
    return processed_df


if __name__ == "__main__":
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = build_processed_dataset()

    output_path = PROCESSED_DIR / "listings_processed.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved processed dataset to: {output_path}")
    print(f"Final shape: {df.shape}")