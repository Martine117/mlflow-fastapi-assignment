"""Resolve the latest completed eligible run once, then download its fixed artifact URI."""
import argparse
import json
from pathlib import Path

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from sklearn.datasets import load_digits

from settings import ARTIFACT, EXPERIMENT, PROJECT


def retrieve(destination):
    client = MlflowClient()
    experiment = client.get_experiment_by_name(EXPERIMENT)
    if experiment is None:
        raise RuntimeError(f'Experiment {EXPERIMENT!r} does not exist; train first')
    runs = client.search_runs(
        [experiment.experiment_id],
        filter_string=f"attributes.status = 'FINISHED' and tags.project = '{PROJECT}' and tags.model_ready = 'true'",
        order_by=['attributes.end_time DESC', 'attributes.start_time DESC', 'attributes.run_id ASC'],
        max_results=1,
    )
    if not runs:
        raise RuntimeError('No completed eligible training run; train first')
    run = runs[0]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    if (destination / ARTIFACT).exists():
        raise RuntimeError('Destination already contains a model; use a fresh directory')
    uri = f'runs:/{run.info.run_id}/{ARTIFACT}'
    path = mlflow.artifacts.download_artifacts(artifact_uri=uri, dst_path=str(destination))
    model = mlflow.sklearn.load_model(path)
    sample = load_digits().data[:1]
    assert model.n_features_in_ == 64
    assert int(model.predict(sample)[0]) in range(10)
    metadata = {'run_id': run.info.run_id, 'artifact_uri': uri,
                'accuracy': run.data.metrics.get('accuracy'), 'end_time': run.info.end_time}
    (destination / 'provenance.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', default='models')
    retrieve(parser.parse_args().destination)
