from typing import Generator

from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings
from src.db.session import SessionERP


# ---------------------------------------------------------
# Engine cache
# ---------------------------------------------------------

_mssql_engines = {}


# ---------------------------------------------------------
# ERP DB
# ---------------------------------------------------------

def get_erp_db() -> Generator[Session, None, None]:
    """
    Core Scoto ERP database.
    """

    db = SessionERP()

    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# MSSQL DB Dependency Factory
# ---------------------------------------------------------

def get_mssql_session(db_key: str):
    """
    Creates a FastAPI dependency for a specific MSSQL database.

    Usage:

        db: Session = Depends(get_mssql_session("db1"))

        db: Session = Depends(get_mssql_session("db2"))
    """

    def _get_session() -> Generator[Session, None, None]:

        # ---------------------------------------------
        # Get actual database name
        # ---------------------------------------------

        dbname = settings.databases_map.get(db_key)

        if not dbname:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Invalid database key: '{db_key}'. "
                    f"Available keys: "
                    f"{list(settings.databases_map.keys())}"
                ),
            )

        # ---------------------------------------------
        # Create engine only once
        # ---------------------------------------------

        if dbname not in _mssql_engines:

            db_url = settings.get_mssql_url(dbname)

            _mssql_engines[dbname] = create_engine(
                db_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=1800,
            )

        # ---------------------------------------------
        # Create session
        # ---------------------------------------------

        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_mssql_engines[dbname],
        )

        db = session_factory()

        try:
            yield db

        finally:
            db.close()

    return _get_session