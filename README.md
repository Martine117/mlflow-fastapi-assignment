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

Materialize the training dataset first: run `python dataset.py` to regenerate the original public digits data, or `dvc pull data/digits.csv.dvc -r myazure` after configuring Azure. See the DVC extension below.

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

## DVC extension (feature/dvc-integration)

Git versions code and small DVC pointers. DVC versions datasets in its local content-addressed cache and Azure Blob Storage. MLflow/DagsHub continues to track training runs and model artifacts. Training records the digits CSV SHA-256 with each run; Docker still downloads only the model from DagsHub at build time. Azure credentials and raw datasets never enter the Docker context. The original serving endpoint and model selection logic are unchanged.

Install the optional development tooling in your project environment (not in Docker):

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dvc.txt
$env:DVC_SITE_CACHE_DIR = Join-Path $PWD '.dvc/site-cache'
```

`python dataset.py` exports sklearn's original 1797 digits in original order, 64 pixels plus target, with deterministic integer formatting and LF line endings. `train.py` reads this DVC-tracked CSV and fails clearly if it is absent. CI regenerates this public dataset with the pinned sklearn version and tests equality with the original data. It uses no Azure secrets. For historical experiments, restore from DVC rather than regenerating data. `requirements.txt`, FastAPI and Docker are unchanged; DVC is an optional training/development dependency.

### Azure setup

You must create your own storage account and private blob container; the course account and exposed SAS are not used. In https://portal.azure.com:

1. Choose your subscription and create a resource group and Storage account. Choose a globally unique lowercase name, Standard performance and locally redundant storage for this demo; review costs before creating.
2. Open the account → Data storage → Containers. Create a private container such as `dvc-data`. Keep anonymous blob access disabled.
3. Generate a fresh container SAS with Read, Add, Create, Write and List permissions, HTTPS only and a short expiry. Prefer a user delegation SAS if available; your Azure administrator may need to grant storage data access.
4. Run `. .\configure-azure.ps1` in your own PowerShell. Enter account and container names at the prompts, and the SAS only at the hidden prompt. Never paste it in chat. The script sets `AZURE_STORAGE_ACCOUNT` and `AZURE_STORAGE_SAS_TOKEN` only for this shell, and stores only the real remote URL in ignored `.dvc/config.local`. No credentials are written to disk or passed as command arguments.

`myazure` is the default DVC remote. Its checked-in URL is explicitly pending until resource setup. The local URL override survives Git tag switches. No Azure secrets are needed in GitHub Actions. Close the shell after use or remove `Env:AZURE_STORAGE_SAS_TOKEN` and `Env:AZURE_STORAGE_ACCOUNT`. Do not print credential environment variables or enable debug logs.

### Dataset versions and commands

`data/digits.csv` is for training. `data/dvc_demo.csv` is solely the course exercise: tag `dvc-demo-v1` references header `id,score` plus records `1,80` and `2,90`; tag `dvc-demo-v2` adds `3,95`. Both CSVs are Git-ignored, and their `.dvc` pointers are committed. These tags are local until explicit publication approval.

```powershell
.\.venv\Scripts\dvc status
# After intentionally editing data:
.\.venv\Scripts\dvc add data/dvc_demo.csv
git add data/dvc_demo.csv.dvc
git commit -m 'Update demo dataset pointer'
# Upload all tagged versions, not only the current version:
.\.venv\Scripts\dvc push --all-tags -r myazure
.\.venv\Scripts\dvc pull -r myazure
.\.venv\Scripts\dvc status -c -r myazure
```

From a clean named branch, run `.\azure-roundtrip.ps1` after Azure setup. It pushes both tags, uses a fresh temporary cache for each pull, verifies exact contents and row counts, and returns to the starting branch. It keeps proof caches for inspection and does not delete cloud objects. Its Azure operations remain unverified until your account is configured.

For the manual experiment, save your branch name, switch to each tag, pull, verify and return:

```powershell
$originalBranch = git branch --show-current
git switch --detach dvc-demo-v1
.\.venv\Scripts\dvc pull -r myazure
.\.venv\Scripts\python verify_dvc.py --version 1
git switch --detach dvc-demo-v2
.\.venv\Scripts\dvc pull -r myazure
.\.venv\Scripts\python verify_dvc.py --version 2
git switch $originalBranch
.\.venv\Scripts\dvc pull -r myazure
```

Until Azure exists, replace `dvc pull` with `dvc checkout` to restore from the populated local cache. This proves local restoration only. `verify_dvc.py` checks exact demo contents, pointer changes, Git exclusions and DVC configuration. Avoid `dvc gc` during this exercise because historical objects are required. Never commit the course PDF, local configuration, environments, datasets or caches.

References: [DVC Azure authentication](https://doc.dvc.org/user-guide/data-management/remote-storage/azure-blob-storage), [Azure container SAS setup](https://learn.microsoft.com/azure/cognitive-services/translator/document-translation/create-sas-tokens?tabs=Containers).
