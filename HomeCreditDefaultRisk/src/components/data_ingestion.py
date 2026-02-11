import os
import json
import uuid
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from src.components.snowflake_client import SnowflakeClient, SnowflakeConfig
from src.components.training_logger import log_run_start, log_run_end
from logger import logging
from exception import CustomException
import sys


DATASET_FQN = "HOME_CREDIT_DB.OPS.V_TRAINING_DATASET"


@dataclass
class DataIngestionConfig:
    artifacts_dir: str = os.path.join("artifacts", "training")
    training_view_fqn: str = DATASET_FQN

    test_size: float = 0.2
    random_state: int = 42
    stratify_col: str = "TARGET"

    def paths_for_run(self, run_id: str) -> Dict[str, str]:
        run_dir = os.path.join(self.artifacts_dir, run_id)
        return {
            "run_dir": run_dir,
            "raw": os.path.join(run_dir, "raw.parquet"),
            "train": os.path.join(run_dir, "train.parquet"),
            "test": os.path.join(run_dir, "test.parquet"),
            "manifest": os.path.join(run_dir, "manifest.json"),
        }


def _ensure_dir(file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


def _dataset_fingerprint(df: pd.DataFrame) -> str:

    schema_str = "|".join([f"{c}:{str(df[c].dtype)}" for c in df.columns])
    base = f"rows={len(df)}|cols={df.shape[1]}|{schema_str}"

    sample = df
    if "SK_ID_CURR" in df.columns:
        sample = df.sort_values("SK_ID_CURR", kind="mergesort")
    sample = sample.head(1000)

    payload = base.encode("utf-8") + sample.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def ingest_training_dataset(sf: SnowflakeClient) -> Tuple[pd.DataFrame, str, int, int]:

    df = sf.fetch_pandas(f"SELECT * FROM {DATASET_FQN};")
    dataset_hash = _dataset_fingerprint(df)
    row_count, col_count = int(len(df)), int(df.shape[1])
    return df, dataset_hash, row_count, col_count


def run_training_ingestion() -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    cfg = DataIngestionConfig()
    paths = cfg.paths_for_run(run_id)

    try:
        logging.info("Starting training ingestion run_id=%s", run_id)

        sf_cfg = SnowflakeConfig.from_env()
        with SnowflakeClient(sf_cfg) as sf:
            df, dataset_hash, row_count, col_count = ingest_training_dataset(sf)

            # Contract checks
            if "SK_ID_CURR" not in df.columns:
                raise ValueError("SK_ID_CURR missing from training dataset.")
            if cfg.stratify_col not in df.columns:
                raise ValueError(f"{cfg.stratify_col} missing from training dataset.")
            if df[cfg.stratify_col].isna().any():
                raise ValueError("TARGET has NULL values. Training cannot proceed.")

            # Log start (single source of truth)
            log_run_start(
                sf=sf,
                run_id=run_id,
                dataset_table=cfg.training_view_fqn,
                dataset_hash=dataset_hash,
                row_count=row_count,
                col_count=col_count,
            )

            # Persist raw
            _ensure_dir(paths["raw"])
            df.to_parquet(paths["raw"], index=False)

            # Split
            train_set, test_set = train_test_split(
                df,
                test_size=cfg.test_size,
                random_state=cfg.random_state,
                stratify=df[cfg.stratify_col],
            )

            _ensure_dir(paths["train"])
            _ensure_dir(paths["test"])
            train_set.to_parquet(paths["train"], index=False)
            test_set.to_parquet(paths["test"], index=False)

            manifest = {
                "run_id": run_id,
                "dataset_table": cfg.training_view_fqn,
                "dataset_hash": dataset_hash,
                "row_count": row_count,
                "col_count": col_count,
                "train_rows": int(len(train_set)),
                "test_rows": int(len(test_set)),
                "params": {
                    "test_size": cfg.test_size,
                    "random_state": cfg.random_state,
                    "stratify_col": cfg.stratify_col,
                },
                "artifacts": {
                    "raw_data_path": paths["raw"],
                    "train_data_path": paths["train"],
                    "test_data_path": paths["test"],
                },
            }

            _ensure_dir(paths["manifest"])
            with open(paths["manifest"], "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            # Log end
            log_run_end(
                sf=sf,
                run_id=run_id,
                status="SUCCESS",
                metrics={
                    "ingest_rows": row_count,
                    "ingest_cols": col_count,
                    "train_rows": int(len(train_set)),
                    "test_rows": int(len(test_set)),
                },
                params=manifest["params"],
                artifacts={
                    **manifest["artifacts"],
                    "manifest_path": paths["manifest"],
                },
            )

        return {
            "run_id": run_id,
            "raw_data_path": paths["raw"],
            "train_data_path": paths["train"],
            "test_data_path": paths["test"],
            "manifest_path": paths["manifest"],
        }

    except Exception as e:
        logging.error("Training ingestion failed run_id=%s err=%s", run_id, str(e))

        # Best-effort DB log
        try:
            sf_cfg = SnowflakeConfig.from_env()
            with SnowflakeClient(sf_cfg) as sf:
                log_run_end(sf=sf, run_id=run_id, status="FAILED", error_message=str(e))
        except Exception:
            pass

        raise CustomException(e, sys)
