# HomeCreditDefaultRisk #

# Batch Feature Pipeline (S3 → Snowflake → Airflow) #

Production-style batch pipeline to build ML-ready feature marts from the Home Credit Default Risk dataset.

## What this project does
**Data/feature pipeline**
- S3 (raw CSVs) → Snowflake **BRONZE** (raw tables)
- BRONZE → **SILVER** (typed + aggregated features)
- SILVER → **GOLD** (final marts)
  - `GOLD.TRAINING_DATASET`
  - `GOLD.SCORING_DATASET`

**Orchestration**
- Airflow DAG triggers Snowflake stored procedures in order:
  1) Bronze load
  2) Silver build
  3) Gold build
  4) DQ gates (fails if checks fail)

## Repo layout (minimal)
```text
HomeCreditDefaultRisk/
├─ dags/
│  └─ homecredit_feature_pipeline_dag.py
├─ sql/                      # optional: store SQL for each layer
├─ src/                      # future: training/scoring code
├─ configs/                  # config-driven approach (future expansion)
└─ README.md
