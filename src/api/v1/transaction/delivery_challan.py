
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.schemas.transaction import (
    DeliveryChallanCreate,
    DeliveryChallanUpdate,
)
from src.services.delivery_challan_service import DeliveryChallanService


router = APIRouter(
    prefix="/delivery-challans",
    tags=["Transaction - Delivery Challan"],
)


@router.get("")
def get_delivery_challans(
    search: Optional[str] = Query(default=None),
    return_type: Optional[str] = Query(default=None),
    fin_year: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=500, description="Items per page"),
    sort_by: Optional[str] = Query(default=None, description="Column to sort by"),
    sort_order: Optional[str] = Query(default="desc", description="Sort direction ('asc' or 'desc')"),
    all: bool = Query(default=False, description="When True, fetch all records"),
    db: Session = Depends(get_mssql_session("db2")),
):
    return DeliveryChallanService.get_all(
        db=db,
        search=search,
        return_type=return_type,
        fin_year=fin_year,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        fetch_all=all,
    )


@router.get("/{delivery_no:path}")
def get_delivery_challan(
    delivery_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    data = DeliveryChallanService.get_by_no(
        db=db,
        delivery_no=delivery_no,
    )

    return {
        "success": True,
        "data": data,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_delivery_challan(
    payload: DeliveryChallanCreate,
    db: Session = Depends(get_mssql_session("db2")),
):
    delivery_no = DeliveryChallanService.create(
        db=db,
        payload=payload,
    )

    return {
        "success": True,
        "message": "Delivery Challan created successfully.",
        "delivery_no": delivery_no,
    }


@router.put("/{delivery_no:path}")
def update_delivery_challan(
    delivery_no: str,
    payload: DeliveryChallanUpdate,
    db: Session = Depends(get_mssql_session("db2")),
):
    DeliveryChallanService.update(
        db=db,
        delivery_no=delivery_no,
        payload=payload,
    )

    return {
        "success": True,
        "message": "Delivery Challan updated successfully.",
        "delivery_no": delivery_no,
    }


@router.delete("/{delivery_no:path}")
def delete_delivery_challan(
    delivery_no: str,
    db: Session = Depends(get_mssql_session("db2")),
):
    DeliveryChallanService.delete(
        db=db,
        delivery_no=delivery_no,
    )

    return {
        "success": True,
        "message": "Delivery Challan deleted successfully.",
        "delivery_no": delivery_no,
    }
