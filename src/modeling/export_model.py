import json
from pathlib import Path

import joblib
import pandas as pd
import numpy as np

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

import sys
from pathlib import Path

PROJECT_ROOT = Path.cwd()# .parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.paths import PROCESSED_DIR, ROOT_DIR
from src.modeling.pipeline import MODEL_FEATURES, build_flat_price_pipeline


MODELS_DIR = ROOT_DIR / "models"


def regression_metrics(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    return {
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "r2": round(float(r2), 4),
        "mape": round(float(mape), 2),
    }


def build_model_metadata(df, metrics):
    return {
        "model_name": "Barcelona flat price valuation pipeline",
        "model_type": "XGBoost Regressor",
        "target": "value",
        "features": MODEL_FEATURES,
        "metrics": metrics,
        "training_rows": int(df.shape[0]),
        "neighborhoods": sorted(df["level8"].dropna().unique().tolist()),
        "energy_letters": sorted(df["energy_letter"].dropna().unique().tolist()),
        "environment_letters": sorted(df["environment_letter"].dropna().unique().tolist()),
        "floor_values": sorted(df["floor_desc"].dropna().unique().tolist()),
    }


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(PROCESSED_DIR / "listings_processed.csv")
    df = df[df["value"].notna()]
    df = df[df["surface"].notna()]
    df = df[df["surface"] > 0]
    df = df[df["level8"].notna()].reset_index(drop=True)

    X = df[MODEL_FEATURES].copy()
    y = df["value"].copy()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=76)

    pipeline = build_flat_price_pipeline(random_state=76)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    metrics = regression_metrics(y_test, y_pred)

    model_path = MODELS_DIR / "flat_price_pipeline.joblib"
    metadata_path = MODELS_DIR / "model_metadata.json"

    joblib.dump(pipeline, model_path)

    metadata = build_model_metadata(df, metrics)
    metadata_path.write_text(json.dumps(metadata, indent=4, ensure_ascii=False), encoding="utf-8")

    print(f"Saved model pipeline to: {model_path}")
    print(f"Saved model metadata to: {metadata_path}")
    print("Evaluation metrics:")
    print(metrics)


if __name__ == "__main__":
    main()