import json

import mlflow
import pytest
from mlflow.tracking import MlflowClient

from retrieve_model import retrieve
from settings import EXPERIMENT, PROJECT


def test_latest_completed_run_ignores_failed_and_unready(tmp_path):
    if not mlflow.get_tracking_uri().startswith('file:'):
        pytest.skip('Decoy run test runs only against local file tracking')
    client = MlflowClient()
    experiment = client.get_experiment_by_name(EXPERIMENT)
    eligible = client.search_runs(
        [experiment.experiment_id],
        filter_string=f"attributes.status = 'FINISHED' and tags.project = '{PROJECT}' and tags.model_ready = 'true'",
        order_by=['attributes.end_time DESC', 'attributes.start_time DESC', 'attributes.run_id ASC'],
        max_results=1,
    )[0]
    decoys = []
    try:
        for status, ready in [('FAILED', 'true'), ('FINISHED', 'false')]:
            run = client.create_run(experiment.experiment_id, tags={'project': PROJECT, 'model_ready': ready})
            decoys.append(run.info.run_id)
            client.set_terminated(run.info.run_id, status)
        retrieve(tmp_path)
        metadata = json.loads((tmp_path / 'provenance.json').read_text())
        assert metadata['run_id'] == eligible.info.run_id
        assert (tmp_path / 'model' / 'MLmodel').is_file()
    finally:
        for run_id in decoys:
            client.delete_run(run_id)
