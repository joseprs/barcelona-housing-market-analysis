import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score


def regression_metrics(y_true, y_pred) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE (%)": mape,
        "R2": r2,
    }


def metrics_table(results: dict) -> pd.DataFrame:
    return (
        pd.DataFrame(results)
        .T
        .reset_index()
        .rename(columns={"index": "model"})
    )


def prediction_results(y_true, y_pred) -> pd.DataFrame:
    return pd.DataFrame({
        "actual_value": y_true,
        "predicted_value": y_pred,
        "absolute_error": np.abs(y_true - y_pred),
        "percentage_error": np.abs((y_true - y_pred) / y_true) * 100,
    })