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


COLUMNS_TO_DROP = [
    "transactions", "transaction_type", "periodicity_id", "energyCertificate",
    "surfaceLand", "countryId", "level1Id", "level2Id", "level3Id",
    "level4Id", "level5Id", "level6Id", "level7Id", "level8Id",
    "conservationState", "orientation", "hotWater", "heating", "antiquity"
]


DUPLICATE_SUBSET = [
    "value", "energy_value", "energy_letter", "environment_value",
    "rooms", "bathrooms", "surface", "floor", "upperLevel"
]


def remove_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]


def rename_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=RENAME_COLUMNS)


def convert_amenities_to_boolean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    existing_cols = [col for col in BOOL_FEATURES_COLS if col in df.columns]

    for col in existing_cols:
        df[col] = np.where(df[col].fillna(0) > 0, True, False)

    return df


def filter_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    base_mask = (
        df["value"].notna()
        & (df["value"] > 0)
        & df["surface"].notna()
        & (df["surface"] > 0)
        & (df["surface"] < 1000)
    )

    if "energy_value" in df.columns:
        base_mask = base_mask & (df["energy_value"].fillna(0) < 999)

    return df[base_mask]


def drop_unused_columns(df: pd.DataFrame) -> pd.DataFrame:
    existing_cols = [col for col in COLUMNS_TO_DROP if col in df.columns]
    return df.drop(columns=existing_cols)


def drop_listing_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    existing_subset = [col for col in DUPLICATE_SUBSET if col in df.columns]
    return df.drop_duplicates(subset=existing_subset, keep="first").reset_index(drop=True)


def add_price_per_sqm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["price_per_sqm"] = df["value"] / df["surface"]
    return df


def prepare_listings_dataset(df: pd.DataFrame, apply_outlier_filter: bool = True) -> pd.DataFrame:
    df = rename_raw_columns(df)
    df = convert_amenities_to_boolean(df)
    df = filter_invalid_rows(df)
    df = drop_unused_columns(df)

    if apply_outlier_filter:
        df = remove_outliers_iqr(df, column="value")

    df = drop_listing_duplicates(df)
    df = add_price_per_sqm(df)

    return df.reset_index(drop=True)