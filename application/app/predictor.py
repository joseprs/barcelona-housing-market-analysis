import json
from pathlib import Path
from typing import Dict, Any

import joblib
import pandas as pd

from application.app.schemas import FlatFeatures


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "flat_price_pipeline.joblib"
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"


class FlatPricePredictor:
    def __init__(self, model_path: Path = MODEL_PATH, metadata_path: Path = METADATA_PATH):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.pipeline = joblib.load(model_path)
        self.metadata = self._load_metadata(metadata_path)

    @staticmethod
    def _load_metadata(metadata_path: Path) -> Dict[str, Any]:
        if metadata_path.exists():
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        return {}

    @staticmethod
    def _to_model_dataframe(features: FlatFeatures) -> pd.DataFrame:
        data = features.model_dump()

        record = {
            "rooms": data["rooms"],
            "bathrooms": data["bathrooms"],
            "surface": data["surface"],
            "level8": data["level8"],
            "energy_letter": data["energy_letter"],
            "environment_letter": data["environment_letter"],
            "energy_value": data["energy_value"],
            "environment_value": data["environment_value"],
            "floor_desc": data["floor_desc"],
            "elevator": data["elevator"],
            "Aire acondicionado": data["air_conditioning"],
            "Piscina": data["pool"],
        }

        return pd.DataFrame([record])

    def predict(self, features: FlatFeatures) -> Dict[str, Any]:
        input_df = self._to_model_dataframe(features)
        prediction = float(self.pipeline.predict(input_df)[0])

        return {
            "predicted_price": round(prediction, 2),
            "predicted_price_rounded": int(round(prediction)),
            "predicted_price_per_sqm": round(prediction / features.surface, 2),
        }