import pandas as pd
import numpy as np
from unidecode import unidecode


SELECTED_FEATURES = [
    "rooms",
    "bathrooms",
    "surface",
    "level8",
    "energy_letter",
    "environment_letter",
    "energy_value",
    "environment_value",
    "floor_desc",
    "elevator",
    "Aire acondicionado",
    "Piscina",
]


CATEGORICAL_FEATURES = [
    "level8",
    "energy_letter",
    "environment_letter",
    "floor_desc",
]


def remove_accents(value):
    if isinstance(value, str):
        return unidecode(value)
    return value


def clean_categorical_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "level8" in df.columns:
        df["level8"] = (
            df["level8"]
            .str.replace(r"[ '.,-]", "_", regex=True)
            .apply(remove_accents)
        )

    if "floor_desc" in df.columns:
        df["floor_desc"] = (
            df["floor_desc"]
            .str.replace("ª", "", regex=False)
            .str.replace(" ", "", regex=False)
            .apply(remove_accents)
        )

    if "antiquity_desc" in df.columns:
        df["antiquity_desc"] = (
            df["antiquity_desc"]
            .apply(remove_accents)
            .str.replace(r"anos|\s", "", regex=True)
        )

    return df


def prepare_modeling_base(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "level6" in df.columns:
        df = df.drop(columns=["level6"])
    if "level8" in df.columns:
        df = df[df["level8"].notna()].reset_index(drop=True)
    return df


def create_modeling_dataset(df: pd.DataFrame):
    df = prepare_modeling_base(df)
    df = clean_categorical_values(df)

    X = df[SELECTED_FEATURES].copy()
    y = df["value"].copy()

    X_encoded = pd.get_dummies(X, columns=CATEGORICAL_FEATURES, drop_first=True)

    return X_encoded, y, df