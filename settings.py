import os

EXPERIMENT = os.getenv('MLFLOW_EXPERIMENT_NAME', 'RandomForest_Digits')
PROJECT = 'mlflow-fastapi-assignment'
ARTIFACT = 'model'
