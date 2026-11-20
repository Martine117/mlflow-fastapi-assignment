# MLflow digits classifier

A Random Forest handwritten-digit classifier with DVC dataset versioning, MLflow tracking on DagsHub, and a FastAPI prediction service. Docker downloads the latest eligible model during the image build and serves it locally at runtime.

## Install and train

Use Python 3.13 and PowerShell from the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python dataset.py
. .\configure-dagshub.ps1
.\.venv\Scripts\python train.py
.\.venv\Scripts\python retrieve_model.py
.\.venv\Scripts\python -m pytest -q
```

The DagsHub script prompts privately for your token and configures tracking at `https://dagshub.com/Martine117/mlflow-digits.mlflow` for the current shell. View runs in the repository's Experiments tab.

Training uses all 1797 public sklearn digits, an 80/20 split with seed 42, and two Random Forest configurations: 20 trees/depth 5 and 100 trees/depth 10. Each run logs parameters, accuracy, model signature and dataset SHA-256.

Retrieval selects the newest FINISHED run with this project's ready tag, ordered by completion time, start time and run ID. It downloads a fixed `runs:/<run_id>/model` artifact and records provenance in `models/provenance.json`. Latest means most recently completed, not highest accuracy. Retrieval requires a fresh destination; use `--destination models-new` for another copy.

For local tracking, set `MLFLOW_TRACKING_URI` to an absolute file URI before training, such as `file:///C:/work/mlruns`.

## Run the API

```powershell
.\.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

In another PowerShell window:

```powershell
$body = @{ instances = @( ,(@(0) * 64) ) } | ConvertTo-Json -Depth 4
Invoke-RestMethod -Uri http://127.0.0.1:8000/predict -Method Post -ContentType 'application/json' -Body $body
```

`POST /predict` is the only application route; documentation routes are disabled. Supply 1?100 samples, each containing exactly 64 finite numeric pixels in row-major 8x8 order, between 0 and 16. Invalid input returns HTTP 422. A successful response looks like `{"predictions":[5]}`; the class depends on the input. The blank sample above is a smoke test.

## Docker

Start Docker Desktop with Linux containers. In the authenticated DagsHub shell:

```powershell
docker build --no-cache --secret id=mlflow_username,env=MLFLOW_TRACKING_USERNAME --secret id=mlflow_password,env=MLFLOW_TRACKING_PASSWORD -t digits:latest .
docker run --rm -p 127.0.0.1:8000:8000 digits:latest
```

BuildKit mounts credentials only for the build-time model download. The final image contains the model and provenance, with no runtime credentials needed. Use `--no-cache` to rerun latest-model selection after new training.

To verify predictions without network access, stop the foreground container and run:

```powershell
docker run -d --network none --name digits digits:latest
docker cp smoke.py digits:/tmp/smoke.py
docker exec digits python /tmp/smoke.py
docker rm -f digits
```

## DVC and Azure Blob Storage

Git stores code and `.dvc` pointers; DVC stores dataset contents in its local cache and Azure. MLflow separately stores training runs and model artifacts on DagsHub. Neither datasets nor Azure credentials enter the Docker build context.

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dvc.txt
$env:DVC_SITE_CACHE_DIR = Join-Path $PWD '.dvc/site-cache'
.\.venv\Scripts\dvc status
```

The coursework remote is `myazure`, account `wut2026`, URL `azure://dvc`. Access requires permission and a valid container SAS. Enter credentials privately in your own shell:

```powershell
$env:AZURE_STORAGE_ACCOUNT = 'wut2026'
$azureSecret = Read-Host 'Authorized container SAS (hidden)' -AsSecureString
try {
    $env:AZURE_STORAGE_SAS_TOKEN = ([System.Net.NetworkCredential]::new('', $azureSecret).Password).TrimStart('?')
} finally { Remove-Variable azureSecret }
.\.venv\Scripts\dvc pull -r myazure
```

Alternatively, existing Git-ignored `.dvc/config.local` credentials can be used. Never print or commit this file. `configure-azure.ps1` supports a different account/container and uses the project subdirectory in that container; its storage path differs from the shared coursework root.

`data/digits.csv` is the training dataset. Regenerate it with `dataset.py` for the original public data, or use DVC to retrieve the recorded version. After intentionally changing a dataset:

```powershell
.\.venv\Scripts\dvc add data/dvc_demo.csv
git add data/dvc_demo.csv.dvc
git commit -m 'Update demo dataset pointer'
.\.venv\Scripts\dvc push -r myazure
.\.venv\Scripts\dvc status -c -r myazure
```

### Restore demo versions

The separate demo CSV has two records in v1 and three in v2. Its tags are local; after cloning, create missing tags with `git tag dvc-demo-v1 5d343cf` and `git tag dvc-demo-v2 4ab4231`.

From a clean named branch, with Azure credentials configured:

```powershell
.\azure-roundtrip.ps1
```

The helper uploads tagged data, pulls each version into a fresh cache, verifies row contents, and returns to the starting branch. Only run it with authorized storage access. For local-only restoration, select a tag with `git switch --detach dvc-demo-v1`, run `dvc checkout`, and run `python verify_dvc.py --version 1`; repeat for v2, then switch back to your original branch and run `dvc checkout`. Avoid garbage collection while historical versions are needed.

## GitHub Actions and credentials

CI regenerates the public dataset, trains against a local MLflow store and runs tests. Main, feature-branch pushes and manual runs also build Docker, test predictions with networking disabled and upload provenance. Pull requests skip the credential-dependent Docker job. Images are not pushed to a registry.

Set repository secrets `MLFLOW_TRACKING_USERNAME` and `MLFLOW_TRACKING_PASSWORD` for DagsHub downloads. Azure secrets are not required by CI. Keep tokens, `.env` files, local DVC configuration, caches and model files out of Git. Close authenticated shells after use, or remove `Env:MLFLOW_TRACKING_PASSWORD` and `Env:AZURE_STORAGE_SAS_TOKEN`.
