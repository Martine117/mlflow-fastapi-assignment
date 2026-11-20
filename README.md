# MLflow digits assignment

Random Forest digit classification adapted from the supplied notebook. Uses sklearn's public built-in digits dataset, a fixed 80/20 split and seed 42. Trains both notebook configurations (20 trees/depth 5 and 100 trees/depth 10). The unrelated supplied CSV and assignment attachments are deliberately excluded.

## Setup and authentication (PowerShell)

Run these commands from this project directory. Python 3.13 is used locally and in Docker/CI.

Alternatively, run `. .\configure-dagshub.ps1` after creating the environment to set all three tracking variables with a hidden token prompt.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:MLFLOW_TRACKING_URI = 'https://dagshub.com/Martine117/mlflow-digits.mlflow'
$env:MLFLOW_TRACKING_USERNAME = 'Martine117'
$credential = Read-Host 'DagsHub access token' -AsSecureString
$env:MLFLOW_TRACKING_PASSWORD = [System.Net.NetworkCredential]::new('', $credential).Password
Remove-Variable credential
```

Create a token in your DagsHub account settings (Tokens). Enter it only at the hidden prompt. Do not put it in source files, command arguments, Git, screenshots or chat. The environment contains the token for this shell session and child processes; close the shell or remove the variable when done. No dagshub SDK login or persistent credential file is needed.

## Train and retrieve

```powershell
.\.venv\Scripts\python train.py
.\.venv\Scripts\python retrieve_model.py
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open your DagsHub repository's Experiments tab to see both runs, accuracy, parameters, signatures and model artifacts. Training tags a model ready only after logging completes. Retrieval searches this experiment for FINISHED runs with project and ready tags, ordered by end time descending, start time descending and run ID ascending. It downloads `runs:/<run_id>/model` from the first result. This defines latest as most recently completed, not highest accuracy. A missing/corrupt latest artifact fails the build rather than silently selecting an older model. Registry aliases and stages are not required; run artifacts provide an immutable identity. The PDF discusses registry operations, but the supplied notebook itself logs run artifacts.

`models/provenance.json` records the selected run and accuracy. Use a fresh destination for each retrieval, e.g. `python retrieve_model.py --destination models-new`. Models are trusted serialized Python objects: download only from your own trusted repository. Local model files are ignored by Git and excluded from Docker's build context.

For offline/local tracking tests, use a fresh shell and set `MLFLOW_TRACKING_URI` to an absolute `file:///C:/.../mlruns` URI instead. Then train, retrieve and test in the same way. This verifies behavior locally but does not establish DagsHub connectivity.

## Build and verify Docker

Start Docker Desktop with Linux containers. Use the authenticated shell above:

```powershell
docker build --no-cache --secret id=mlflow_username,env=MLFLOW_TRACKING_USERNAME --secret id=mlflow_password,env=MLFLOW_TRACKING_PASSWORD -t digits:latest .
docker run -d --network none --name digits digits:latest
docker cp smoke.py digits:/tmp/smoke.py
docker exec digits python /tmp/smoke.py
docker exec digits cat /app/models/provenance.json
docker rm -f digits
docker run --rm -p 8000:8000 digits:latest
```

BuildKit mounts credentials only during the download RUN instruction; credentials are never build arguments or image environment variables. A separate final stage copies only downloaded model artifacts and provenance. The app loads `/app/models/model` from disk; it fails on startup if absent. The network-disabled smoke test proves inference needs neither credentials nor downloads. `--no-cache` is essential when asking for latest: Docker cannot detect remote training changes or secret changes. This is also set in CI. Builds deliberately depend on DagsHub availability.

## POST /predict

Only one route is registered. Docs, ReDoc and OpenAPI routes are disabled. Input is `instances`, a nonempty batch of at most 100 digits, each exactly 64 finite numeric pixels in row-major 8x8 order, each between 0 and 16. Strings, booleans, nulls and extra fields are rejected with HTTP 422. Output is one integer class (0–9) per digit.

In a second PowerShell window:

```powershell
$body = @{ instances = @( ,(@(0) * 64) ) } | ConvertTo-Json -Depth 4
Invoke-RestMethod -Uri http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body $body
```

The blank image is a smoke test, not a meaningful digit. Tests also compare held-out digits against direct model predictions and require accuracy above 0.85.

## GitHub Actions and publication

After approving publication, create a PUBLIC GitHub repository named `mlflow-fastapi-assignment` and upload only the contents of this project directory. Do not upload the parent workspace, virtual environment, source attachments, model folders or credentials.

Under repository Settings → Secrets and variables → Actions, add repository secrets:

* `MLFLOW_TRACKING_USERNAME`: `Martine117`
* `MLFLOW_TRACKING_PASSWORD`: your DagsHub access token

The workflow trains and tests against a local MLflow store on all pull requests. Pushes to main and manual runs additionally build with DagsHub secrets, verify predictions inside a network-disabled container, and upload model provenance. Pull requests never receive download credentials. It builds locally on the runner and does not push an image to a registry. Train on DagsHub before triggering the Docker job.

Remove credentials from your shell after use:

```powershell
Remove-Item Env:MLFLOW_TRACKING_PASSWORD
```

References: [DagsHub experiment tracking](https://dagshub.com/docs/feature_guide/experiment_tracking/), [MLflow run search](https://mlflow.org/docs/latest/ml/search/search-runs/), [Docker build secrets](https://docs.docker.com/build/building/secrets/).
