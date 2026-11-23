
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.master import ItemCreate, ItemUpdate
from src.services import itemmaster_services

router = APIRouter(
    prefix="/items",
    tags=["Master - Item Master"],
)


@router.get("")
def read_items(
    search: Optional[str] = Query(default=None),
    product_type: Optional[str] = Query(default=None),
    page: Optional[int] = Query(default=None, ge=1, description="Page number (1-based)"),
    page_size: Optional[int] = Query(default=None, ge=1, le=500, description="Items per page"),
    sort_by: Optional[str] = Query(default=None, description="Column to sort by"),
    sort_order: Optional[str] = Query(default="desc", description="Sort direction ('asc' or 'desc')"),
    all: bool = Query(default=False, description="When True, fetch all records"),
    db: Session = Depends(get_mssql_session("db2")),
):
    fetch_all = all or (page is None and page_size is None)
    return itemmaster_services.get_items(
        db=db,
        search=search,
        product_type=product_type,
        page=page or 1,
        page_size=page_size or 20,
        sort_by=sort_by,
        sort_order=sort_order,
        fetch_all=fetch_all,
    )


@router.post("", status_code=201)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return itemmaster_services.create_item(
        db=db,
        payload=payload,
    )


@router.put("/{item_code:path}")
def update_item(
    item_code: str,
    payload: ItemUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    return itemmaster_services.update_item(
        db=db,
        item_code=item_code,
        payload=payload,
    )


@router.delete("/{item_code:path}")
def delete_item(
    item_code: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    return itemmaster_services.delete_item(
        db=db,
        item_code=item_code,
    )
