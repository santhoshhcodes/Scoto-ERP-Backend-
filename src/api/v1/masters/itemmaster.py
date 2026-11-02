
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
    db: Session = Depends(get_mssql_session("db2")),
):
    return itemmaster_services.get_items(
        db=db,
        search=search,
        product_type=product_type,
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


@router.put("/{item_code}")
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


@router.delete("/{item_code}")
def delete_item(
    item_code: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    return itemmaster_services.delete_item(
        db=db,
        item_code=item_code,
    )
