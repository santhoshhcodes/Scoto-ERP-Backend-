from threading import Lock
from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

# Base classes for ORM models
BaseERP = declarative_base()      # For MySQL (scoto_erp_db)
BaseLegacy = declarative_base()   # For MS SQL Server (eSSL/Company DBs)

# -------------------------------------------------------------
# 1. Core MySQL ERP Engine (Fixed instance)
# -------------------------------------------------------------
engine_erp = create_engine(
    settings.mysql_erp_url,
    pool_size=15,
    max_overflow=25,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=(settings.ENVIRONMENT == "development"),
)
SessionERP = sessionmaker(autocommit=False, autoflush=False, bind=engine_erp)


# -------------------------------------------------------------
# 2. Multi-DB MS SQL Server Engine Registry (Thread-Safe Lazy Init)
# -------------------------------------------------------------
class DatabaseRegistry:
    def __init__(self):
        self._engines: Dict[str, any] = {}
        self._sessions: Dict[str, sessionmaker] = {}
        self._lock = Lock()

    def get_session_maker(self, db_key: str) -> sessionmaker:
        if db_key not in settings.databases_map:
            raise KeyError(f"Invalid database key '{db_key}'. Available: {list(settings.databases_map.keys())}")

        dbname = settings.databases_map[db_key]

        # Double-check locking pattern to avoid duplicate engine pools under concurrency
        if db_key not in self._sessions:
            with self._lock:
                if db_key not in self._sessions:
                    engine = create_engine(
                        settings.get_mssql_url(dbname),
                        pool_size=10,
                        max_overflow=20,
                        pool_recycle=1800,
                        pool_pre_ping=True,
                        echo=(settings.ENVIRONMENT == "development"),
                    )
                    self._engines[db_key] = engine
                    self._sessions[db_key] = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        return self._sessions[db_key]

db_registry = DatabaseRegistry()