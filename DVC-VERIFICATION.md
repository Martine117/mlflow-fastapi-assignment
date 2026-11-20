# Local DVC verification

Executed on 2026-11-20 on `feature/dvc-integration`. No changes were pushed or merged.

Passed:

- DVC 3.67.1 with dvc-azure 3.1.1 installed in the isolated tooling environment at `../dvc-azure-assignment/.venv`; the existing MLflow Python environment was not changed. Install `requirements-dvc.txt` in your preferred development environment for ongoing use.
- Deterministic export of all 1797 digits; exported arrays equal sklearn originals exactly.
- `dvc add` for training data and both demo versions. `dvc status` detected the demo edit before adding v2 and reported up to date afterward.
- Local tags `dvc-demo-v1` and `dvc-demo-v2`; different content hashes for the two demo versions.
- Switching to each tag and `dvc checkout` restored exactly two and three demo records. `verify_dvc.py` passed for both; returned to feature branch.
- Training with the exported data in an isolated local MLflow store: accuracies 0.9389 and 0.9722. Latest eligible model retrieved successfully into ignored `.verification/models`, leaving existing `models/` unchanged.
- Entire pytest suite: **15 passed, 3 dependency deprecation warnings**, using the isolated local MLflow store/model. This includes all existing tests and both new dataset tests.
- Candidate source files reviewed for secret patterns and excluded artifacts before commits. CSVs, cache, local config and environments excluded from Git.
- No differences against main in FastAPI, Dockerfile, runtime requirements or Docker context allowlist. CI adds deterministic dataset export before its existing training sequence; no Azure secrets added.

Environment issues resolved:

- The sandbox could not resolve this repository through DVC's Windows Git library; DVC operations ran with the required local-user access. This exact repository path was added to that user's Git safe-directory list.
- DVC site cache was directed to ignored `.dvc/site-cache` to avoid ProgramData permissions.
- Initial pytest attempts encountered temporary-directory permissions; rerunning with a writable ignored workspace base directory passed.

Pending:

- Azure storage account and private container creation, fresh credentials, real remote URL.
- `dvc push --all-tags`, Azure `dvc pull` and fresh-cache Azure restoration. No cloud success is claimed. `myazure` is a pending placeholder, not a configured usable account.
- A new authenticated Docker build and GitHub Actions run were not executed for this branch. Existing Docker/serving files are unchanged; prior image success was reported by the user.
- No GitHub publication is authorized for this extension yet.
