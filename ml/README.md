# Forecasting research component

Offline, script-driven Phase 4 research uses the openly licensed UCI Online Retail II dataset. Training runs separately from web requests. The proposal remains the requirements authority; this implements research objectives 1 and 2. No Phase 5 risk/replenishment/dashboard behavior is included.

Run from the project root using Python 3.12.14. `ml/requirements.txt` pins direct ML libraries; `ml/requirements-lock.txt` records the complete actual shared Python environment, including backend dependencies and transitives. For an exact reproduction in a fresh virtual environment, install the lock file. Raw customer data, processed data and binary models are ignored by Git; preserve attribution and avoid publishing customer identifiers.

```powershell
.\.venv\Scripts\python.exe scripts/create_phase4_reproduction_workspace.py .local/reproduction-1
Set-Location .local/reproduction-1
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r ml/requirements-lock.txt
.\.venv\Scripts\python.exe scripts/download_phase4_dataset.py
.\.venv\Scripts\python.exe -m ml.cli prepare
.\.venv\Scripts\python.exe -m ml.cli eda
.\.venv\Scripts\python.exe -m ml.cli features
.\.venv\Scripts\python.exe -m pytest ml -c ml/pytest.ini
.\.venv\Scripts\python.exe -m ml.cli validate
.\.venv\Scripts\python.exe -m ml.cli final
.\.venv\Scripts\python.exe -m ml.cli verify-reproduction
.\.venv\Scripts\python.exe -m ml.reporting
.\.venv\Scripts\python.exe -m ml.cli infer --sku 20700 --origin 2011-11-10 --horizon 28
```

Acquisition validates exact archive/workbook hashes. `prepare` validates both worksheets, schema/dimensions/dates, reports rejected transactions, selects the seeded training-only cohort, exports daily development history and a separately sealed final-label file. `eda` analyses initial training only; `features` exports shifted training features. `validate` fits/tunes the predeclared configurations using two expanding chronological validation origins, exports matched predictions and **freezes selection**. `final` fits the frozen finalists on train+validation, predicts without test labels, durably marks test access, evaluates once and exports the selected artifact plus metadata. `verify-reproduction` reloads the registered artifact, reproduces its predictions and recalculates all final scores without modifying selection. `reporting` renders actual recorded research results and plots.

Completed experiments cannot be retuned/overwritten. The current workspace already holds frozen/evaluated results; use `verify-reproduction` or `infer` here. Run a full independent reproduction only in a fresh checkout/output workspace with its own records. Do not delete the frozen selection or test-access guard to retry tuning. If final evaluation is interrupted after the guard is written, stop for research review. A reproduced run's timings, creation timestamp and binary bytes may differ; data/parameters/splits and forecasts must agree within the recorded numeric tolerance. There is no Git commit yet; executable source SHA-256 fingerprints are recorded in frozen selection.

`artifacts/<run_id>/selected.joblib` is the actual saved selected model. Its adjacent JSON files contain features, preprocessing, model identity and evaluation. The external registry and tracked predictions/metrics are in `docs/research/results`. Registry paths are project-relative. Load only this trusted internal artifact; joblib is unsafe for arbitrary user files. Version/hash/vocabulary/feature checks refuse incompatible artifacts.

The Python callable `ml.experiment.forecast_contract` and `infer` return Pydantic `forecast-v1` JSON. It includes a namespaced research SKU, origin, 1–28 consecutive daily points, model identity/version, training cutoff and timezone-aware created timestamp. Unknown SKU/insufficient history errors are explicit. No inference HTTP endpoint or MySQL model schema was added. A future application integration must deliberately map dataset StockCodes to operational products, supply compatible history and persist forecasts as needed. UK GBP observed-sales forecasts do not establish Kenyan retail performance.

See `docs/research/DATASET.md`, `EXPERIMENT_PROTOCOL.md`, `EDA.md`, `MODEL_COMPARISON.md`, `FINAL_MODEL.md`, and `docs/test-results/phase4-*` for execution evidence. The pipeline is not notebook-dependent.
