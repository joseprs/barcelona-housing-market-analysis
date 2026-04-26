from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from xgboost import XGBRegressor


def train_baseline_model(X_train, y_train):
    model = DummyRegressor(strategy="median")
    model.fit(X_train, y_train)
    return model


def train_random_forest_model(X_train, y_train):
    model = RandomForestRegressor(
        n_estimators=300,
        random_state=76,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def train_xgboost_model(X_train, y_train):
    model = XGBRegressor(
        random_state=76,
        objective="reg:squarederror",
    )
    model.fit(X_train, y_train)
    return model


def optimize_xgboost_model(X_train, y_train):
    param_grid = {
        "n_estimators": [200, 300, 400, 500],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.05, 0.1, 0.2],
        "subsample": [0.8, 0.9, 1.0],
        "colsample_bytree": [0.8, 0.9, 1.0],
    }

    model = XGBRegressor(
        random_state=76,
        objective="reg:squarederror",
    )

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_grid,
        n_iter=50,
        scoring="neg_mean_absolute_error",
        cv=5,
        verbose=1,
        random_state=42,
        n_jobs=-1,
    )

    search.fit(X_train, y_train)

    return search.best_estimator_, search.best_params_