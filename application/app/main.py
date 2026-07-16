from pathlib import Path
from typing import Optional, Union

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from application.app.predictor import FlatPricePredictor
from application.app.schemas import FlatFeatures


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

app = FastAPI(title="Barcelona Flat Price Prediction API", version="1.0.0")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
predictor = FlatPricePredictor()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    context = {
        "request": request,
        "metadata": predictor.metadata,
        "result": None,
        "form": None,
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )


@app.post("/predict", response_class=HTMLResponse)
def predict_form(
    request: Request,
    rooms: int = Form(...),
    bathrooms: int = Form(...),
    surface: float = Form(...),
    level8: str = Form(...),
    floor_desc: Optional[str] = Form(None),
    energy_letter: Optional[Union[str, int, float]] = Form(None),
    environment_letter: Optional[Union[str, int, float]] = Form(None),
    energy_value: Optional[float] = Form(None),
    environment_value: Optional[float] = Form(None),
    elevator: bool = Form(False),
    air_conditioning: bool = Form(False),
    pool: bool = Form(False),
):
    features = FlatFeatures(
        rooms=rooms,
        bathrooms=bathrooms,
        surface=surface,
        level8=level8,
        floor_desc=floor_desc,
        energy_letter=energy_letter,
        environment_letter=environment_letter,
        energy_value=energy_value,
        environment_value=environment_value,
        elevator=elevator,
        air_conditioning=air_conditioning,
        pool=pool,
    )

    result = predictor.predict(features)

    context = {
        "request": request,
        "metadata": predictor.metadata,
        "result": result,
        "form": features.model_dump(),
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )


@app.post("/api/predict")
def predict_api(features: FlatFeatures):
    return predictor.predict(features)