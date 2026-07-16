import pandas as pd
import numpy as np

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer

from xgboost import XGBRegressor
from unidecode import unidecode


NUMERIC_FEATURES = ["rooms","bathrooms","surface","energy_value","environment_value"]
CATEGORICAL_FEATURES = ["level8","energy_letter","environment_letter","floor_desc"]
BOOLEAN_FEATURES = ["elevator","Aire acondicionado","Piscina"]

MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BOOLEAN_FEATURES


def to_integer_array(values):
    return values.astype(int)


class HousingFeatureCleaner(BaseEstimator, TransformerMixin):
    """
    Cleans raw model input data before preprocessing.
    This transformer is part of the saved model pipeline, which ensures that
    the same cleaning logic is used during both training and inference.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        for col in MODEL_FEATURES:
            if col not in X.columns:
                X[col] = np.nan

        X = X[MODEL_FEATURES]

        if "level8" in X.columns:
            X["level8"] = X["level8"].astype("object").where(X["level8"].notna(), np.nan).apply(self._clean_neighborhood)

        if "floor_desc" in X.columns:
            X["floor_desc"] = X["floor_desc"].astype("object").where(X["floor_desc"].notna(), np.nan).apply(self._clean_floor)

        for col in BOOLEAN_FEATURES:
            X[col] = X[col].fillna(False).astype(int)

        return X

    @staticmethod
    def _remove_accents(value):
        if isinstance(value, str):
            return unidecode(value)
        return value

    @classmethod
    def _clean_neighborhood(cls, value):
        if not isinstance(value, str):
            return value
        value = cls._remove_accents(value)
        return value.replace("'", "_").replace(".", "_").replace(",", "_").replace("-", "_").replace(" ", "_")

    @classmethod
    def _clean_floor(cls, value):
        if not isinstance(value, str):
            return value
        value = cls._remove_accents(value)
        return value.replace("ª", "").replace(" ", "")


def build_flat_price_pipeline(random_state: int = 76) -> Pipeline:
    """
    Builds the production-ready valuation pipeline.
    The pipeline receives raw listing features and applies all preprocessing
    internally before generating a price prediction.
    """

    numeric_pipeline = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    boolean_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("to_int", FunctionTransformer(to_integer_array, feature_names_out="one-to-one")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
            ("boolean", boolean_pipeline, BOOLEAN_FEATURES),
        ]
    )

    model = XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=random_state,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("cleaner", HousingFeatureCleaner()),
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )