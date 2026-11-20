# Local DVC verification

Executed on 2026-11-20 on `feature/dvc-integration`. Local verification completed before publication; main has not been merged.

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

Azure coursework verification (2026-11-20):

- User confirmed professor authorization to use shared account `wut2026`, private container `dvc`, remote `myazure` at `azure://dvc`, and explicitly authorized the exposed course credential for this exercise.
- Credential extracted directly from the local PDF without displaying it and stored using DVC's local configuration API exclusively in Git-ignored `.dvc/config.local`. No credential is included here or in tracked source. Initial configuration attempts failed because the API was not given the DVC directory; explicitly supplying `.dvc` resolved that local setup error before Azure access.
- Read-only Azure prefix listing succeeded before uploads. Authentication succeeded.
- Targeted `dvc push` for the training and demo pointers succeeded for both tagged demo versions. Only these coursework datasets were targeted: digits (265285 bytes), demo v1 (19 bytes) and demo v2 (24 bytes). No all-repository upload, garbage collection, deletion or unrelated blob operation was run.
- First fresh-cache v1 pull returned exit 1. A diagnostic fresh-cache v2 pull succeeded and fetched two files. Retrying with `dvc pull --force` limited to the two coursework pointers succeeded for both v1 and v2. Force applies to local workspace checkout, not overwriting unrelated Azure data.
- Each successful version pull used a previously nonexistent cache directory. Verified both downloaded objects against DVC content hashes, then verified exact demo rows: two for v1 and three for v2. These were Azure downloads, not original-cache restores.
- Restored the current feature-branch pointer, dataset v2 and original cache configuration. Branch remained `feature/dvc-integration`; main unchanged.
- Automated tests rerun: **15 passed, 3 dependency deprecation warnings**.

Pending:

- No remaining Azure verification blocker observed in this session. The course credential remains exposed and time-limited; future operations depend on its continuing validity and authorization.
- A new authenticated Docker build and GitHub Actions run were not executed for this branch. Existing Docker/serving files are unchanged; prior image success was reported by the user.
- Feature-branch publication is authorized. Main must not be merged. GitHub Actions results are reported separately after pushing.
