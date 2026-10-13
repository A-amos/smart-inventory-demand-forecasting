# Executed Phase 4 forecasting research

The proposal sections 3.6/3.13/4.4.1 and Appendix V are implemented through a real UCI Online Retail II case study. Objectives 1 and 2 have actual descriptive and forecasting evidence. Objective 3 inventory decision rules and integrated objective 4 evaluation remain later phases. No questionnaire or synthetic operational test data is used to train.

- [Confirmed dataset, source, CC BY terms, snapshot and geography](research/DATASET.md)
- [Training-only actual EDA and plots/tables](research/EDA.md)
- [Protocol defined before training](research/EXPERIMENT_PROTOCOL.md)
- [Validation selection versus frozen final comparison](research/MODEL_COMPARISON.md)
- [Selected artifact, inference contract and limitations](research/FINAL_MODEL.md)
- [Executable acquisition/preprocessing/training/evaluation/export commands](../ml/README.md)

Machine-readable runs and predictions: research/results. Actual automated/live/build evidence: test-results/phase4-*. Raw/processed datasets and model binaries exist locally and are Git-ignored. The selected artifact is trusted internal joblib only, with hash/feature/runtime compatibility checks. Source/feature/library fingerprints are recorded because no Git commit exists. MAPE is omitted for zero/intermittent sales; MAE/RMSE use identical observations and were recalculated from saved predictions. UK/GBP observed-sales results do not prove Kenyan performance. No Phase 5 procurement/replenishment/risk/dashboard behavior was implemented.
