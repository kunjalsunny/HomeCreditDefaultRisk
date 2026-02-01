from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

SNOWFLAKE_CONN_ID = "snowflake_homecredit"


def call_snowflake_proc_and_fail(sql: str, conn_id: str = SNOWFLAKE_CONN_ID) -> str:
    hook = SnowflakeHook(snowflake_conn_id = conn_id)
    conn = hook.get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute(sql)
            row=cur.fetchone()
        finally:
            cur.close()
    finally:
        conn.close()
    
    result = str(row[0]) if row and row[0] is not None else ""
    if result.upper().startswith("FAILED"):
        raise RuntimeError(f"Snowflake Pipeline step failed: {result}")
    
    return result



default_args  = {
    "owner":"data-eng",
    "depends_on_past":False,
    "retries":2,
    "retry_delay":timedelta(minutes=5),
}

with DAG(
    dag_id="homecredit_feature_pipeline",
    default_args = default_args,
    description = "S3 -> Snowflake(Bronze->Silver->Gold)",
    start_date = datetime(2026, 2, 1),
    schedule_interval = None,
    catchup=False,
    tags=["homecredit","snowflake","features"]
) as dag:
    
    bronze_load = PythonOperator(
        task_id = "bronze_load_s3_to_bronze",
        python_callable = call_snowflake_proc_and_fail,
        op_kwargs = {
            "sql":"CALL HOME_CREDIT_DB.OPS.SP_RUN_BRONZE_LOAD('airflow bronze load');"
        },
    )

    silver_load = PythonOperator(
        task_id = "bronze_to_silver_features",
        python_callable = call_snowflake_proc_and_fail,
        op_kwargs = {
            "sql":"CALL HOME_CREDIT_DB.OPS.SP_RUN_SILVER_LOAD('airflow silver load');"
        },
    )

    gold_load = PythonOperator(
        task_id = "silver_to_gold_feature_marts",
        python_callable = call_snowflake_proc_and_fail,
        op_kwargs = {
            "sql":"CALL HOME_CREDIT_DB.OPS.SP_RUN_GOLD_BUILD('airflow gold load');"
        },
    )

    dq_gates = PythonOperator(
        task_id="dq_gates_fail_if_bad",
        python_callable = call_snowflake_proc_and_fail,
        op_kwargs = {
            "sql":"CALL HOME_CREDIT_DB.OPS.SP_RUN_DQ_GATES('airflow dq gates');"
        },
    )

    bronze_load >> silver_load >> gold_load >> dq_gates

