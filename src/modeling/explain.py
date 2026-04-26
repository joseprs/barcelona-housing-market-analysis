import pandas as pd
import numpy as np


def extract_feature_group(feature_name: str) -> str:
    if feature_name.startswith("level8"):
        return "neighborhood"
    if feature_name.startswith("floor_desc"):
        return "floor"
    if feature_name.startswith("environment_l"):
        return "environment_letter"
    if feature_name.startswith("energy_l"):
        return "energy_letter"
    return feature_name


def feature_importance_table(model, feature_names) -> pd.DataFrame:
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    df_importance = pd.DataFrame({
        "feature": feature_names[indices],
        "importance": importances[indices],
    })

    df_importance["feature_group"] = df_importance["feature"].apply(extract_feature_group)

    return df_importance


def grouped_feature_importance(df_importance: pd.DataFrame) -> pd.DataFrame:
    return (
        df_importance
        .groupby("feature_group", as_index=False)["importance"]
        .mean()
        .sort_values("importance", ascending=False)
    )