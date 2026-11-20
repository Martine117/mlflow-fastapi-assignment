import os
from contextlib import asynccontextmanager

import mlflow.sklearn
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated

Pixel = Annotated[float, Field(strict=True, ge=0, le=16, allow_inf_nan=False)]
Digit = Annotated[list[Pixel], Field(min_length=64, max_length=64)]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    instances: Annotated[list[Digit], Field(min_length=1, max_length=100)]


@asynccontextmanager
async def lifespan(app):
    # Only a local filesystem path is accepted: never fetch at container startup.
    from pathlib import Path
    path = Path(os.getenv('MODEL_PATH', 'models/model')).resolve()
    if not (path / 'MLmodel').is_file():
        raise RuntimeError('Bundled model missing; retrieve the model before serving')
    app.state.model = mlflow.sklearn.load_model(str(path))
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.post('/predict')
def predict(body: PredictRequest):
    values = np.asarray(body.instances, dtype=np.float64)
    return {'predictions': app.state.model.predict(values).astype(int).tolist()}
