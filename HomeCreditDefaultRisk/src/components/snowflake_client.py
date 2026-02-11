import os
from dataclasses import dataclass
from typing import List, Any, Dict, Optional, Sequence

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SnowflakeConfig:
    account: str
    user: str
    password: str
    role: str
    warehouse: str
    database: str
    schema: str

    @staticmethod
    def from_env() -> "SnowflakeConfig":
        required = [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "SNOWFLAKE_ROLE",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
        ]

        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise RuntimeError(f"Missing required field:{missing}")
        
        return SnowflakeConfig(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            role=os.environ["SNOWFLAKE_ROLE"],
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            database=os.environ["SNOWFLAKE_DATABASE"],
            schema=os.environ["SNOWFLAKE_SCHEMA"],
        )
    
class SnowflakeClient:
    def __init__(self, cfg: SnowflakeConfig):
        self.cfg = cfg
        self._conn = None
    
    def __enter__(self) ->"SnowflakeConfig":
        self._conn = snowflake.connector.connect(
            account=self.cfg.account,
            user=self.cfg.user,
            password=self.cfg.password,
            role=self.cfg.role,
            warehouse=self.cfg.warehouse,
            database=self.cfg.database,
            schema=self.cfg.schema,
        )
        return self

    def __exit__(self, exc_type, exc,tb)->None:
        if self._conn is not None:
            self._conn.close()

    def execute(self, sql:str, params: Optional[Dict[str,Any]]=None) -> None:
        assert self._conn is not None, "Not connected"
        with self._conn.cursor() as cur:
            cur.execute(sql, params or {})

    def fetch_pandas(self, sql: str):
        assert self._conn is not None, "Not connected"
        with self._conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetch_pandas_all()
    
    def fetch_one(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Sequence[Any]]:
        assert self._conn is not None, "Not connected"
        with self._conn.cursor() as cur:
            cur.execute(sql, params or {})
            return cur.fetchone()
