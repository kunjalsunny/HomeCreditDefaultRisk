import json
from typing import Any, Dict, Optional

from src.components.snowflake_client import SnowflakeClient

INSERT_RUNNING = """
INSERT INTO HOME_CREDIT_DB.ML.TRAINING_RUNS
(RUN_ID, DATASET_TABLE, DATASET_HASH, ROW_COUNT, COL_COUNT, TRAIN_START_TS, STATUS)
VALUES
(%(run_id)s, %(dataset_table)s, %(dataset_hash)s, %(row_count)s, %(col_count)s, CURRENT_TIMESTAMP(), 'RUNNING');
"""

UPDATE_FINAL = """
UPDATE HOME_CREDIT_DB.ML.TRAINING_RUNS
SET
  TRAIN_END_TS  = CURRENT_TIMESTAMP(),
  MODEL_NAME    = %(model_name)s,
  MODEL_VERSION = %(model_version)s,
  MLFLOW_RUN_ID = %(mlflow_run_id)s,
  METRICS       = PARSE_JSON(%(metrics_json)s),
  PARAMS        = PARSE_JSON(%(params_json)s),
  ARTIFACTS     = PARSE_JSON(%(artifacts_json)s),
  STATUS        = %(status)s,
  ERROR_MESSAGE = %(error_message)s
WHERE RUN_ID = %(run_id)s;
"""

def log_run_start(
    sf: SnowflakeClient,
    run_id: str,
    dataset_table: str,
    dataset_hash: str,
    row_count: int,
    col_count: int,
) -> None:
    sf.execute(
        INSERT_RUNNING,
        {
            "run_id": run_id,
            "dataset_table": dataset_table,
            "dataset_hash": dataset_hash,
            "row_count": row_count,
            "col_count": col_count,
        },
    )

def log_run_end(
    sf: SnowflakeClient,
    run_id: str,
    status: str,
    model_name: Optional[str] = None,
    model_version: Optional[str] = None,
    mlflow_run_id: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    artifacts: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
) -> None:
    sf.execute(
        UPDATE_FINAL,
        {
            "run_id": run_id,
            "status": status,
            "model_name": model_name,
            "model_version": model_version,
            "mlflow_run_id": mlflow_run_id,
            "metrics_json": json.dumps(metrics or {}),
            "params_json": json.dumps(params or {}),
            "artifacts_json": json.dumps(artifacts or {}),
            "error_message": error_message,
        },
    )
