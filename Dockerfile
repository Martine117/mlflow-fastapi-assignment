# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS model-fetch
ARG MLFLOW_TRACKING_URI=https://dagshub.com/Martine117/mlflow-digits.mlflow
ARG MLFLOW_EXPERIMENT_NAME=RandomForest_Digits
COPY retrieve_model.py settings.py ./
RUN --mount=type=secret,id=mlflow_username,required=true \
    --mount=type=secret,id=mlflow_password,required=true \
    MLFLOW_TRACKING_USERNAME="$(cat /run/secrets/mlflow_username)" \
    MLFLOW_TRACKING_PASSWORD="$(cat /run/secrets/mlflow_password)" \
    MLFLOW_TRACKING_URI="$MLFLOW_TRACKING_URI" \
    MLFLOW_EXPERIMENT_NAME="$MLFLOW_EXPERIMENT_NAME" \
    python retrieve_model.py --destination /bundle

FROM base AS runtime
COPY app.py ./
COPY --from=model-fetch /bundle /app/models
RUN useradd --uid 10001 --create-home appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
