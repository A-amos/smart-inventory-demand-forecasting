"""Check preserved actual evidence before recording Phase 4 completion."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.common import RESEARCH, environment, now, read_json, sha256, source_fingerprints, write_json
from ml.contracts import ForecastOutput


def suite(name):
    root = ET.parse(ROOT / f'docs/test-results/phase4-{name}.xml').getroot()
    groups = list(root.iter('testsuite'))
    totals = {key: sum(int(group.attrib.get(key, 0)) for group in groups)
              for key in ['tests', 'failures', 'errors', 'skipped']}
    if not totals['tests'] or any(totals[key] for key in ['failures', 'errors', 'skipped']):
        raise ValueError(f'{name} suite did not fully execute/pass: {totals}')
    return totals


def update(path, old, new):
    path = ROOT / path
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise ValueError(f'Expected documentation text missing: {path.name}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


def main():
    tests = {name: suite(name) for name in ['backend', 'ml', 'frontend']}
    final = read_json(RESEARCH / 'results/final-test.json')
    validation = read_json(RESEARCH / 'results/validation.json')
    frozen = read_json(RESEARCH / 'results/frozen-selection.json')
    registry = read_json(RESEARCH / 'results/model-registry.json')
    source = read_json(RESEARCH / 'results/preprocessing.json')
    eda = read_json(RESEARCH / 'eda/summary.json')
    reproduction = read_json(RESEARCH / 'results/reproduction.json')
    validation_reproduction = read_json(ROOT / 'docs/test-results/phase4-validation-reproduction.json')
    assert validation_reproduction['passed'] and len(validation_reproduction['records']) == 12
    reacquisition = (ROOT / 'docs/test-results/phase4-dataset-reacquisition.txt').read_text()
    assert 'verified against existing manifest' in reacquisition
    contract = ForecastOutput.model_validate(read_json(RESEARCH / 'results/last-inference.json'))
    live = read_json(ROOT / 'docs/test-results/phase4-live.json')
    compose = [__import__('json').loads(line) for line in (ROOT / 'docs/test-results/phase4-compose.jsonl').read_text().splitlines()]
    migration = (ROOT / 'docs/test-results/phase4-migration.txt').read_text()
    build = (ROOT / 'docs/test-results/phase4-frontend-build.txt').read_text(encoding='utf-8')
    selected = frozen['selected']
    assert final['selected_by_validation_only'] == registry['candidate'] == selected
    assert frozen['source_fingerprints'] == source_fingerprints(), 'Research sources changed after freeze'
    assert frozen['environment']['packages'] == environment()['packages']
    assert sha256(RESEARCH / 'results/frozen-selection.json') == final['frozen_selection_sha256']
    assert sha256(ROOT / registry['artifact_path']) == registry['artifact_sha256']
    assert reproduction['passed'] and reproduction['model_id'] == registry['model_id']
    assert contract.model_id == registry['model_id'] and len(contract.points) == 28
    assert all(check['passed'] for check in live['checks']) and len(live['checks']) == 15
    assert {row['Service'] for row in compose} == {'db', 'backend', 'frontend', 'migrate'}
    assert all(row['State'] == 'running' for row in compose if row['Service'] != 'migrate')
    assert next(row for row in compose if row['Service'] == 'db')['Health'] == 'healthy'
    assert next(row for row in compose if row['Service'] == 'migrate')['ExitCode'] == 0
    assert '7cf0674f24d9 (head)' in migration and 'No new upgrade operations detected.' in migration
    assert 'built in' in build and '32 modules transformed' in build
    assert 'No broken requirements found.' in (ROOT / 'docs/test-results/phase4-pip-check.txt').read_text()
    for document in ['DATASET.md', 'EDA.md', 'EXPERIMENT_PROTOCOL.md', 'MODEL_COMPARISON.md', 'FINAL_MODEL.md']:
        assert (RESEARCH / document).is_file()
    assert len(final['scores']) == 4 and len(validation['scores']) == 6
    assert all(score['observations'] == 1680 for score in final['scores'].values())
    assert all(score['observations'] == 3360 for score in validation['scores'].values())
    summary = {'phase': 4, 'gate_passed': True, 'recorded_at_utc': now(), 'tests': tests,
               'selected_by_validation': selected, 'validation_scores': validation['scores'],
               'final_test_scores': final['scores'], 'model_id': registry['model_id'],
               'actual_live_checks': len(live['checks']), 'artifact_reproduction_passed': reproduction['passed'],
               'validation_numerical_reproduction_passed': validation_reproduction['passed'],
               'dataset_reacquisition_passed': True,
               'frontend_build_passed': True, 'compose_verified': True, 'schema_changes': False,
               'migration_head': '7cf0674f24d9', 'inference_endpoint_introduced': False,
               'inference_boundary': 'executed saved-artifact Python/CLI forecast-v1 contract',
               'next_phase_started': False, 'dataset': 'UCI Online Retail II',
               'source_sha256': source['source_sha256'], 'environment_lock_sha256': sha256(ROOT / 'ml/requirements-lock.txt')}
    write_json(ROOT / 'docs/test-results/phase4-summary.json', summary)
    rows = '| Candidate | Validation MAE | Validation RMSE | Final MAE | Final RMSE |\n| --- | ---: | ---: | ---: | ---: |\n'
    for name in validation['ranking']:
        v, t = validation['scores'][name], final['scores'].get(name)
        rows += f"| {name} | {v['mae']:.6f} | {v['rmse']:.6f} | {format(t['mae'], '.6f') if t else 'Not frozen finalist'} | {format(t['rmse'], '.6f') if t else '—'} |\n"
    score = final['scores'][selected]
    log = f'''## 2026-10-01 — Phase 4 research exit gate passed

### Implemented scope and actual research findings

Implemented the proposal/roadmap objective 1/2 offline research package only: source validation, auditable preprocessing, initial-training EDA, shifted features, fixed-origin recursive forecasting, baseline/RF/XGBoost comparison, validation-only selection, one frozen final holdout, selected artifact export/reload and forecast-v1 Python/CLI contract. Training never runs inside ordinary application requests. No Phase 5 risk, replenishment, procurement, dashboard or forecasting HTTP endpoint was added; no database schema changed.

Dataset: **UCI Online Retail II**, DOI 10.24432/C5CG6D, CC BY 4.0, public download without external accounts. Obtained 2026-09-30T22:14:04.092443+00:00 (2026-10-01 Nairobi). Exact source/terms/files/hashes are in docs/research/DATASET.md and dataset-manifest.json. M5 competition terms were reviewed; the open transaction-level alternative was explicitly selected before development/training. UK gift/wholesale online retail and GBP prices do not establish Kenyan physical-retail performance. Questionnaires and Phase 3 synthetic test files are excluded.

Actual workbook: 1,067,371 × 8 records/columns; two sheets 525,461 and 541,910 rows; dates 2009-12-01 07:45 through 2011-12-09 12:50; 5,305 raw stock codes and 43 destination countries. Valid positive transaction rows: 1,003,214; distinct valid product codes: {source['valid_product_skus_all_periods']:,}. Exclusive rejections: {source['audit']['exclusive_rejections']}. Customer IDs/descriptions are not model features; missing ones do not discard otherwise valid transactions. No category/store/events/promotions labels are supplied or invented. Exact duplicates are removed under a documented export-duplication assumption; legitimate indistinguishable repeated invoice lines are a limitation. Outliers are retained.

Initial-training-only cohort: seed 20261001, 365-day minimum history, >=60 positive days, 20 SKUs from each of three zero-fraction strata; **60 selected SKUs**. Full valid-code exclusion report: {source['cohort_exclusions']}. Expanded the report before freezing to include 194 future-only products; selected cohort/development/test file hashes did not change. Daily zeros after first observation mean no recorded purchase under the complete-export assumption, not proven absent demand. Quantity-weighted GBP prices are forward filled from the past only. Initial training: 37,753 SKU-days; validation: 3,360 targets; final test: 1,680 targets; complete study daily panel: 42,793 observations.

EDA: 26,891 zero training days (71.23%), median demand interval {eda['median_average_demand_interval']:.3f} days, median lag-7 correlation {eda['median_lag7_correlation']:.4f}, all 60 SKUs with price variation, median price/demand Spearman {eda['median_price_demand_spearman']:.4f}. Saturday observed sales are zero in the constant-panel export; monthly/trailing trends and weekday differences are descriptive associations. Retained 4,635 upper-three-IQR flags, maximum selected training daily purchase 7,008 units. Actual plots/tables: docs/research/eda; interpretation: EDA.md. No causal price/promotion or Kenyan-performance finding is invented.

### Validation versus final test

Protocol was fixed before training in ml/protocol.json and EXPERIMENT_PROTOCOL.md: daily retailer-SKU; horizon 28; initial train through 2011-09-15; validation origins 2011-09-15 and 2011-10-13; final origin 2011-11-10, targets 2011-11-11 through 2011-12-08. December 9 incomplete source day was pre-excluded. One-hot SKU vocabulary is training-selected; demand lags 1/7/14/28, shifted rolling mean/std 7/28, known calendar and lagged price/change features are shared by training/inference. Recursive forecasts consume earlier own predictions and fixed-origin price, never future actual sales/prices.

Compared seasonal-naive and mean-28 baselines, RF leaf 5/15 (80 trees, depth 12), XGBoost depth 3/5 (200/150 trees, learning rate .05). Two expanding validation windows tune family configurations and select overall winner by pooled MAE, then RMSE/name. **{selected}** selected/frozen at {frozen['frozen_at_utc']}; final labels accessed only at {read_json(RESEARCH / 'results/final-test-access.json')['opened_at_utc']} after all frozen finalists fit/predicted. No final-test tuning, cohort revision or winner replacement. Every final candidate used exactly the same 1,680 actual SKU/date targets; every validation candidate used the same 3,360. Other hyperparameter configurations were not final-tested. MAPE omitted for mathematically undefined/misleading zero/intermittent demand; no epsilon or hidden positive-only subset.

{rows}
Metrics are units/SKU-day, not percentages. Selected final MAE **{score['mae']:.6f}**, RMSE **{score['rmse']:.6f}**, zero actual days {score['zero_actual_count']}/1680. Full paired predictions, per-SKU scores, worst ten products and fixed training representatives are preserved. Poor forecasts are retained/reported. Exact effective parameters, dependency versions, seeds, timings and feature/source fingerprints are saved. No Git commit exists; source SHA-256 fingerprints replace an invented revision. Artifact: `{registry['artifact_path']}`, SHA-256 `{registry['artifact_sha256']}`; run `{registry['model_id']}`. Artifact reload reproduced 1,680 predictions within absolute tolerance 1e-10 and recalculated all four models' final MAE/RMSE from saved observations. CLI inference generated actual 28-day forecast-v1 JSON for known SKU 20700; schema and example are exported. Research StockCodes remain namespaced and are not silently imported/mapped to live products.

### Actual commands and checks

Commands ran at project root unless noted. Python denotes `.\\.venv\\Scripts\\python.exe`; Docker denotes `C:\\Users\\user\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe`; pnpm denotes the bundled `dependencies\\bin\\fallback\\pnpm.cmd`, using bundled Node 24.19.0 in PATH and `pnpm_config_verify_deps_before_run=false`. Research runtime Python 3.12.14, NumPy 2.2.6, Pandas 2.2.3, sklearn 1.6.1, XGBoost 3.0.2. Direct pins plus complete actual-environment lock saved under ml/.

| Actual command | Observed result / artifact |
| --- | --- |
| `Python -m pip install -r ml/requirements.txt` | Initial sandbox network WinError10013, approved rerun installed pinned libraries; environment-lock recorded with `Python -m pip freeze` |
| `Python scripts/download_phase4_dataset.py` | Initial sandbox network failure, approved public download passed; manifest hashes preserved |
| `Python -m ml.cli prepare` | Workbook schema/count/date/hash verification passed; second run completed full future-only exclusion audit before freeze; phase4-preprocessing.txt |
| `Python -m ml.cli eda`; `Python -m ml.cli features` | Actual training-only figures/tables and shifted training features exported; phase4-eda.txt / phase4-features.txt |
| `Python -m ml.cli validate` | First export failed on XGBoost default NaN parameter metadata; strict tagged metadata fix tested; same configs rerun successfully and frozen; phase4-validation-first.txt / phase4-validation.txt |
| `Python -m ml.cli final` | Four frozen finalists, identical observations, final scores/predictions and selected artifact saved once; phase4-final.txt |
| `Python -m ml.cli verify-reproduction` | Passed artifact hash/version/key/prediction checks and all-model metric recalculation; phase4-reproduction.txt / reproduction.json |
| `Python -m ml.reporting` | Actual five requested research documents/figures, worst products and final model details created; phase4-reports.txt |
| `Python -m ml.cli infer --sku 20700 --origin 2011-11-10 --horizon 28` | Actual saved artifact produced 28 nonnegative daily points and valid forecast-v1 JSON; phase4-inference.txt / last-inference.json |
| `Python -m pytest backend/tests -c backend/pytest.ini --junitxml=docs/test-results/phase4-backend.xml` | **{tests['backend']['tests']} passed**, 1 upstream Starlette/AnyIO deprecation; phase4-backend.txt / XML |
| `Python -m pytest ml -c ml/pytest.ini -q --junitxml=docs/test-results/phase4-ml.xml` | **{tests['ml']['tests']} passed**; chronological ordering, cohort independence, shifted features, recursive future mutations, zeros/missing/unknown/history/horizons, JSON contract, deterministic models/reload, metadata/version/hash/path guards; phase4-ml.txt / XML |
| In frontend: `pnpm test --reporter=junit --outputFile=../docs/test-results/phase4-frontend.xml` | Sandbox esbuild directory denial; approved rerun **{tests['frontend']['tests']} passed**, no failures/errors; phase4-frontend.txt / XML |
| In frontend: `pnpm build` | Same sandbox denial; approved rerun **passed**, 32 modules, 3.06 seconds; phase4-frontend-build.txt |
| `Docker compose up -d`; `Docker compose ps -a --format json` | First sandbox launch StandardOutputEncoding/redirect failure; approved rerun existing services running, MySQL healthy, migration exit 0; phase4-compose.jsonl |
| `Docker compose exec -T backend alembic current`; `... alembic check` | **7cf0674f24d9 (head)**; no new upgrade operations; phase4-migration.txt. No schema change/downgrade |
| `Python scripts/verify_phase1.py` | Approved actual localhost MySQL/API/proxy/session verification: **15 live checks passed**, MySQL 8.4.11; copied non-secret JSON to phase4-live.json |
| `Python -m pip check`; `Python -m compileall -q ml` | Passed; no broken requirements or syntax errors; phase4-pip-check.txt |
| `Python scripts/finalize_phase4.py` | Verified actual artifact/report/test/runtime evidence before generating phase4-summary.json and this gate record |

### Failures, corrections and limits

First validation trained/predicted correctly but strict JSON refused XGBoost's `missing=NaN` default parameter. This was a metadata-format error, not a missing-value substitution in training or a metric. Stopped before freeze/test; tagged only nonfinite estimator-default metadata, kept all forecast/metric JSON strictly finite, added a regression test and reran identical configs. First validation prediction SHA-256 was preserved for comparison. No hyperparameter/split changes followed scores. Network/esbuild/Docker environment failures were rerun with execution approval; no external account, default published credentials or destructive command was used. Some apply_patch context matches failed atomically before a successful edit; a wrong roadmap filename was corrected. Public web download rendering had a size limit, so the explicit public-download Python script was used. Proposal terminal text initially hit cp1252 subscript encoding; UTF-8 reads/outputs resolved inspection. Original DOCX remains unchanged.

Limitations: small fixed 60-SKU cohort, one final 28-day horizon, fewer than two full annual cycles, UK gift/wholesale online context, gross observed purchases rather than stockout-censored latent demand, no inventory availability/store/category/events, past-only weighted transactional GBP prices, unknown/new SKUs rejected, and all-vocabulary contiguous history required at inference. Actual forecasts are fractional; future decision rounding/mapping/storage belongs to Phase 5. No confidence/significance, Kenya fieldwork, participant usability, production hosting or full completed-system claim. Model joblib files and registry must be trusted; hashes do not make arbitrary pickle files safe. Earlier Recharts/dependency review and upstream deprecation remain future deployment work.

**Phase 4 exit gate passed on actual evidence. Stop here. Phase 5 has not begun.** Research docs, real comparison records, test/build/runtime artifacts and this log are complete. Next authorized increment may integrate the verified contract with explicit product mappings, persisted forecasts, explainable inventory decisions and dashboard; it requires a new user instruction.

'''
    log_path = ROOT / 'DEVELOPMENT_LOG.md'
    content = log_path.read_text(encoding='utf-8')
    start = content.index('## 2026-10-01 — Phase 4 research verification in progress')
    end = content.index('## 2026-10-01 — Phase 3 sales and historical import completed', start)
    log_path.write_text(content[:start] + log + content[end:], encoding='utf-8')
    supplemental = f'''### Additional reproduction evidence and corrected setup

`Python scripts/verify_phase4_validation_reproduction.py` independently refit all 12 predeclared candidate/origin combinations without using final labels or changing selection. All 20,160 predictions matched their recorded validation values within 1e-10; largest actual absolute difference **{validation_reproduction['maximum_absolute_prediction_difference']:.3e}**. Parallel floating-point tree accumulation can change CSV bytes at very small precision. The first failed-export table was overwritten on retry; only its byte hash was retained, so exact numerical comparison with that first table is unavailable. Fresh independent refits of the preserved completed validation table were verified; no bit-for-bit tree CSV or binary promise is made.

Found and fixed fresh-checkout setup issues: tracked manifest with ignored raw files previously assumed files existed; downloader now reacquires missing files, verifies saved hashes and preserves original snapshot metadata. The isolated-workspace script copies research sources/terms/protocol and tests without prior processed targets, frozen results, model binaries or credentials. Ran `Python scripts/create_phase4_reproduction_workspace.py .local/phase4-reproduction`, then `Python .local/phase4-reproduction/scripts/download_phase4_dataset.py`. Sandbox socket access failed; approved public reacquisition completed and both original hashes matched. The actual setup and download logs are preserved. Two meaningful setup tests raised the final ML suite to **{tests['ml']['tests']} passed**. A complete independent retraining pipeline in that fresh workspace was not run; existing-record artifact reproduction, all-candidate validation refits and actual raw reacquisition were run. README includes precise isolated rerun commands.

The first `scripts/finalize_phase4.py` invocation occurred while reacquisition was still running; its gate correctly refused completion and wrote an AssertionError trace. Waited for successful hash verification, then reran finalization. First refusal preserved in phase4-finalization-first.txt. No result was inferred from an unfinished process.

'''
    actual_log = log_path.read_text(encoding='utf-8')
    log_path.write_text(actual_log.replace('## 2026-10-01 — Phase 3 sales and historical import completed',
                        supplemental + '## 2026-10-01 — Phase 3 sales and historical import completed', 1), encoding='utf-8')
    update('docs/IMPLEMENTATION_ROADMAP.md', 'Phases 0–3 are now implemented;', 'Phases 0–4 are now implemented;')
    update('docs/IMPLEMENTATION_ROADMAP.md', "This increment stops at Phase 3 under the user's instruction.", "This increment stops at Phase 4 under the user's instruction. Phase 4 research verification passed; Phase 5 remains unimplemented.")
    update('docs/IMPLEMENTATION_ROADMAP.md', 'Research model candidates remain provisional:', 'The executed Phase 4 candidates were:')
    update('docs/IMPLEMENTATION_ROADMAP.md', 'Phase 3 sales/imports are implemented and verified: 112 backend tests, 20 frontend tests, 43 live MySQL/API checks and an actual browser sale/import workflow. Evidence is recorded in DEVELOPMENT_LOG.md and docs/test-results. Stop here: Phase 4 requires a new instruction and dataset/license/horizon confirmation; no ML work was begun.',
           f'Phase 4 research is implemented and verified: UCI Online Retail II, actual training-only EDA, two baselines, RF and XGBoost, validation-selected {selected}, frozen final holdout, reproducible artifact and forecast-v1 Python/CLI contract. {tests["backend"]["tests"]} backend, {tests["ml"]["tests"]} ML and {tests["frontend"]["tests"]} frontend tests pass; frontend build and Compose/MySQL checks pass. See docs/research and phase4-summary.json. Stop here. Phase 5 requires a new user instruction and will deliberately map research forecasts to operational products before decision/dashboard integration.')
    update('README.md', 'Phases 1–3 are implemented and verified:', 'Phases 1–4 are implemented and verified:')
    update('README.md', 'Forecasting research, recommendations and charts remain later phases. No dataset accuracy or completed-system claim is made.',
           'Phase 4 adds genuine offline research: openly licensed UCI Online Retail II, baseline/RF/XGBoost experiments, validation-only selection, frozen final test and a verified saved-model forecast contract. Recommendations, application forecast storage/integration and dashboard remain Phase 5. UK dataset results are not Kenyan retail evidence or a completed-system claim.')
    update('README.md', 'This increment stops at Phase 3; no machine learning work has begun.', 'This increment stops at Phase 4; Phase 5 has not begun. Research commands and limitations are in [ml/README.md](ml/README.md); actual comparisons are in [docs/research/MODEL_COMPARISON.md](docs/research/MODEL_COMPARISON.md).')
    update('docs/ARCHITECTURE.md', 'Planned versioned ML inference', 'Verified offline forecast-v1 Python contract')
    update('docs/ARCHITECTURE.md', 'Planned offline sales experiments', 'Executed offline sales experiments')
    update('docs/ARCHITECTURE.md', '`ml` will own data preparation, time-safe features, model comparison and artifacts.', '`ml` owns verified source preparation, training-only EDA, prior-only features, baseline/RF/XGBoost experiments, frozen evaluation and trusted artifacts. Its Pydantic Python/CLI contract is executed offline; no application inference endpoint was introduced.')
    with (ROOT / 'docs/DATABASE.md').open('a', encoding='utf-8') as file:
        file.write('\n## Phase 4 model boundary\n\nPhase 4 adds no tables or migrations. MySQL remains at 7cf0674f24d9; live alembic check reports no pending upgrade operations. Research model-run/preprocessing/feature/frozen-evaluation metadata and forecast-v1 JSON are versioned files. The trusted binary model lives under ml/artifacts. Research StockCodes are namespaced uci-online-retail-ii and are not automatically MySQL product IDs. Forecast/model/recommendation persistence and explicit SKU/history mapping are deferred to Phase 5. See research/FINAL_MODEL.md and results/forecast-schema.json.\n')
    with (ROOT / 'docs/API.md').open('a', encoding='utf-8') as file:
        file.write('\n## Phase 4 forecast contract\n\nNo forecasting HTTP route was introduced; existing authenticated APIs remain unchanged. The verified callable ml.experiment.forecast_contract and ml.cli infer load the selected trusted artifact and return Pydantic forecast-v1 JSON with namespaced SKU, origin, consecutive 1–28-day points/quantities, model ID/version, trained-through cutoff and created timestamp. Unknown SKU, invalid horizon, inadequate/gapped history and incompatible artifact fail explicitly. JSON Schema/example are in research/results/forecast-schema.json and example-forecast.json. This Python/CLI interface was executed; it is not listed as a deployed HTTP endpoint. Product mapping, persistence and authenticated application integration are Phase 5 work.\n')
    for old, new in [
        ('| TC13 | Sufficient-history forecast | Pending phase 4 |', '| TC13 | Sufficient-history forecast | Passed offline saved-model/CLI contract on 365+ day history; application forecast endpoint deferred |'),
        ('| TC14 | Inadequate-history fallback/error | Pending phase 4 |', '| TC14 | Inadequate-history fallback/error | Passed explicit insufficient/gapped-history and unknown-SKU errors in ML suite |'),
        ('| TC15 | Malformed forecast request | Pending phase 4 |', '| TC15 | Malformed forecast request | Passed callable horizon/schema/origin validation; HTTP route not introduced |'),
        ('| TC16 | Held-out forecast metrics | Pending phase 4; no numerical results |', '| TC16 | Held-out forecast metrics | Passed validation freeze then identical final observations, actual MAE/RMSE and artifact/metric reproduction |')]:
        update('docs/TESTING.md', old, new)
    with (ROOT / 'docs/TESTING.md').open('a', encoding='utf-8') as file:
        file.write(f'\nIndependent refits reproduced every one of 12 validation candidate/origin forecasts (20,160 predictions); maximum absolute difference {validation_reproduction["maximum_absolute_prediction_difference"]:.3e}, tolerance 1e-10, frozen selection unchanged. Byte-for-byte CSV identity is not promised for parallel floating-point tree predictions. Actual dataset reacquisition into an isolated workspace matched both saved hashes without modifying provenance. Additional setup tests validate missing-file reacquisition, corrupted-source refusal, source copying and exclusion of prior frozen results/credentials.\n')
        file.write(f'\n## Phase 4 actual verification\n\nFull backend: **{tests["backend"]["tests"]} passed**; full ML: **{tests["ml"]["tests"]} passed**; full frontend: **{tests["frontend"]["tests"]} passed**. The frontend production build passed (32 modules, 3.06s). Compose/MySQL revision/consistency checks and 15 actual API/session/proxy smoke checks passed. Forecast verification used the real selected binary model and 1,680 saved test predictions; all four models\' metrics were recalculated from saved pairs. The last-inference JSON validates a real 28-day forecast-v1 contract. No inference HTTP endpoint or schema change was introduced. Research tests use synthetic unit fixtures for guards, separately from actual retail experiments; frontend network responses remain mocked. Evidence: phase4-backend.xml, phase4-ml.xml, phase4-frontend.xml, phase4-live.json, phase4-compose.jsonl, phase4-migration.txt, phase4-frontend-build.txt, phase4-summary.json and research/results/reproduction.json. First validation metadata-export failure and sandbox/tooling failures are recorded honestly in the log. Phase 4 passes; TC17–TC22, broader security/performance/browser/participant evaluation remain later phases. No completed 24-case system or Kenyan operational-performance claim.\n')
    (ROOT / 'docs/ML_EXPERIMENTS.md').write_text('# Executed Phase 4 forecasting research\n\nThe proposal sections 3.6/3.13/4.4.1 and Appendix V are implemented through a real UCI Online Retail II case study. Objectives 1 and 2 have actual descriptive and forecasting evidence. Objective 3 inventory decision rules and integrated objective 4 evaluation remain later phases. No questionnaire or synthetic operational test data is used to train.\n\n- [Confirmed dataset, source, CC BY terms, snapshot and geography](research/DATASET.md)\n- [Training-only actual EDA and plots/tables](research/EDA.md)\n- [Protocol defined before training](research/EXPERIMENT_PROTOCOL.md)\n- [Validation selection versus frozen final comparison](research/MODEL_COMPARISON.md)\n- [Selected artifact, inference contract and limitations](research/FINAL_MODEL.md)\n- [Executable acquisition/preprocessing/training/evaluation/export commands](../ml/README.md)\n\nMachine-readable runs and predictions: research/results. Actual automated/live/build evidence: test-results/phase4-*. Raw/processed datasets and model binaries exist locally and are Git-ignored. The selected artifact is trusted internal joblib only, with hash/feature/runtime compatibility checks. Source/feature/library fingerprints are recorded because no Git commit exists. MAPE is omitted for zero/intermittent sales; MAE/RMSE use identical observations and were recalculated from saved predictions. UK/GBP observed-sales results do not prove Kenyan performance. No Phase 5 procurement/replenishment/risk/dashboard behavior was implemented.\n', encoding='utf-8')
    print('All actual Phase 4 evidence verified; docs/log/phase4-summary.json updated. Phase 5 not started.')


if __name__ == '__main__':
    main()
