import pandas as pd
import numpy as np


RENAME_COLUMNS = {
    "orientation.1": "orientation_desc",
    "floor.1": "floor_desc",
    "antiquity.1": "antiquity_desc",
    "conservationState.1": "conservationState_desc",
    "hotWater.1": "hotWater_type_desc",
    "heating.1": "heating_desc",
}


BOOL_FEATURES_COLS = [
    "furnished", "parking", "Aire acondicionado", "Parquet", "Horno",
    "Microondas", "Serv. portería", "Balcón", "Lavadero", "Armarios",
    "Calefacción", "Suite - con baño", "Nevera", "Puerta Blindada",
    "Terraza", "Electrodomésticos", "Alarma", "Cocina Equipada",
    "Lavadora", "Cocina Office", "Patio", "Videoportero", "Piscina",
    "Gres Cerámica", "Jardín Privado", "Trastero", "Internet", "Domótica",
    "TV", "Ascensor interior", "Sistema Video vigilancia CCTV 24h",
    "Z. Comunitaria", "Zona Deportiva", "Zona Infantil",
    "Piscina comunitaria", "Gimnasio", "Baño de huéspedes",
    "Cuarto para el servicio", "Jacuzzi", "Bodega", "Sauna",
    "Cuarto lavado plancha", "Energía Solar", "elevator", "Pista de Tenis"
]


DUPLICATE_SUBSET = [
    "value", "energy_value", "energy_letter", "environment_value",
    "rooms", "bathrooms", "surface", "floor", "upperLevel"
]


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=RENAME_COLUMNS)


def clean_boolean_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    existing_bool_cols = [col for col in BOOL_FEATURES_COLS if col in df.columns]

    for col in existing_bool_cols:
        df[col] = np.where(df[col].fillna(0) > 0, True, False)

    return df


def filter_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df[
        (df["value"].notna()) &
        (df["value"] > 0) &
        (df["surface"].notna()) &
        (df["surface"] > 0) &
        (df["surface"] < 1000)
    ]

    if "energy_value" in df.columns:
        df = df[df["energy_value"].fillna(0) < 999]

    return df


def drop_listing_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    subset_existing = [col for col in DUPLICATE_SUBSET if col in df.columns]
    return df.drop_duplicates(subset=subset_existing).reset_index(drop=True)


def add_price_per_sqm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["price_per_sqm"] = df["value"] / df["surface"]
    return df