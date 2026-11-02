from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict


import os
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_backend_env = os.path.join(_backend_dir, ".env")

class Settings(BaseSettings):
    SECRET_KEY: str = 'scoto_jwt_key_2026'
    ENVIRONMENT: str = "development"

    # MS SQL Server (Hardware / Multi-tenant Company DBs)
    MSSQL_SERVER: str
    MSSQL_PORT: int = 1433
    MSSQL_USER: str
    MSSQL_PASSWORD: str

    # Direct map of dynamic keys
    DB_KEY_DB1: str = "etimetracklite1"
    DB_KEY_DB2: str = "SCOTO_ACC_ERP"


    # MySQL Core ERP
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB_NAME: str = "scoto_erp_db"

    @property
    def databases_map(self) -> Dict[str, str]:
        """Maps client keys to active database names."""
        return {
            "db1": self.DB_KEY_DB1,
            "db2": self.DB_KEY_DB2
        }

    @property
    def mysql_erp_url(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB_NAME}"
        )

    def get_mssql_url(self, dbname: str) -> str:
        return (
            f"mssql+pymssql://{self.MSSQL_USER}:{self.MSSQL_PASSWORD}@"
            f"{self.MSSQL_SERVER}:{self.MSSQL_PORT}/{dbname}"
        )

    model_config = SettingsConfigDict(env_file=_backend_env if os.path.exists(_backend_env) else ".env", extra="ignore")

settings = Settings()