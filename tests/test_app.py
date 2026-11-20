import pytest
from fastapi.testclient import TestClient
from sklearn.datasets import load_digits
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from app import app


def test_model_and_api():
    with TestClient(app) as client:
        x, y = load_digits(return_X_y=True)
        _, x_test, _, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
        assert accuracy_score(y_test, app.state.model.predict(x_test)) > 0.85
        response = client.post('/predict', json={'instances': x_test[:3].tolist()})
        assert response.status_code == 200
        assert response.json()['predictions'] == app.state.model.predict(x_test[:3]).tolist()
        assert client.get('/docs').status_code == 404
        assert client.get('/openapi.json').status_code == 404
        assert [(r.path, r.methods) for r in app.routes] == [('/predict', {'POST'})]


@pytest.mark.parametrize('body', [
    {}, {'instances': []}, {'instances': [[0]*63]}, {'instances': [[0]*65]},
    {'instances': [[17]*64]}, {'instances': [[-1]*64]},
    {'instances': [['0']*64]}, {'instances': [[True]*64]},
    {'instances': [[None]*64]}, {'instances': [[0]*64], 'extra': 1},
    {'instances': [[0]*64]*101},
])
def test_invalid(body):
    with TestClient(app) as client:
        assert client.post('/predict', json=body).status_code == 422
