# Barcelona Flat Price Prediction App

This folder contains the application layer for the Barcelona Housing Market Intelligence project.

The app exposes the trained flat valuation model through:

- a simple web form for manual predictions
- a JSON API endpoint for programmatic predictions
- a health-check endpoint
- a Dockerized execution environment

The model artifact is loaded from:

    models/flat_price_pipeline.joblib

The metadata used to populate form dropdowns is loaded from:

    models/model_metadata.json

---

## Local Run

From the project root:

    uvicorn application.app.main:app --reload

Then open:

    http://127.0.0.1:8000

API documentation:

    http://127.0.0.1:8000/docs

---

## Docker Run

Build the image from the project root:

    docker build -f application/Dockerfile -t bcn-flat-price-app .

Run the container:

    docker run -p 8000:8000 bcn-flat-price-app

Then open:

    http://127.0.0.1:8000

---

## API Endpoint

Prediction endpoint:

    POST /api/predict

Example request:

    {
      "rooms": 3,
      "bathrooms": 2,
      "surface": 85,
      "level8": "Dreta de l'Eixample",
      "floor_desc": "3ª planta",
      "energy_letter": null,
      "environment_letter": null,
      "energy_value": 80,
      "environment_value": 80,
      "elevator": true,
      "air_conditioning": false,
      "pool": false
    }

Example response:

    {
      "predicted_price": 335820.4,
      "predicted_price_rounded": 335820,
      "predicted_price_per_sqm": 4197.89
    }

---

## Disclaimer

The prediction is based on housing listing data and should be interpreted as an estimated asking price, not as a certified property valuation or financial recommendation.
