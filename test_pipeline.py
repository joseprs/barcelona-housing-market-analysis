import joblib
import pandas as pd

pipeline = joblib.load("models/flat_price_pipeline.joblib")

sample_input = pd.DataFrame([
    {
        "rooms": 3,
        "bathrooms": 2,
        "surface": 85,
        "level8": "Dreta de l'Eixample",
        "energy_letter": 3,
        "environment_letter": 3,
        "energy_value": 120,
        "environment_value": 30,
        "floor_desc": "2ª planta",
        "elevator": True,
        "Aire acondicionado": True,
        "Piscina": False,
    }
])

prediction = pipeline.predict(sample_input)[0]

print(f"Predicted asking price: {prediction:,.0f} €")