import uuid

from src.components.snowflake_client import SnowflakeClient, SnowflakeConfig
from src.components.training_logger import log_run_start, log_run_end
from src.components.data_ingestion import DATASET_FQN

from exception import CustomException
from logger import logging
import sys


def run_training_ingest_smoke() -> str:
    run_id = str(uuid.uuid4())
    cfg = SnowflakeConfig.from_env()

    logging.info("Smoke pipeline started run_id=%s dataset=%s", run_id, DATASET_FQN)

    with SnowflakeClient(cfg) as sf:
        try:
            row_count = int(sf.fetch_one(f"SELECT COUNT(*) FROM {DATASET_FQN};")[0])
            col_count = int(sf.fetch_one(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                                         f"WHERE TABLE_SCHEMA = 'OPS' AND TABLE_NAME = 'V_TRAINING_DATASET';")[0])

            dataset_hash = f"smoke-count={row_count}-cols={col_count}"
            logging.info(f"smoke-count={row_count}-cols={col_count}")

            log_run_start(
                sf=sf,
                run_id=run_id,
                dataset_table=DATASET_FQN,
                dataset_hash=dataset_hash,
                row_count=row_count,
                col_count=col_count,
            )

            logging.info("Inserted TRAINING_RUNS start for run_id=%s", run_id)

            log_run_end(
                sf=sf,
                run_id=run_id,
                status="SUCCESS",
                metrics={"smoke_ok": True, "rows": row_count, "cols": col_count},
            )

            logging.info("Updated TRAINING_RUNS end SUCCESS for run_id=%s", run_id)

            return run_id

        except Exception as e:
            logging.exception("Smoke pipeline FAILED run_id=%s", run_id)
            try:
                log_run_end(sf=sf, run_id=run_id, status="FAILED", error_message=str(e))
            except Exception:
                pass
            raise CustomException(e,sys) 
        
if __name__ == "__main__":
    run_training_ingest_smoke()
