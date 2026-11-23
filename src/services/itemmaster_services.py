
from urllib.parse import unquote
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.helpers.pagination import paginate_raw_sql
from src.helpers.sorting import resolve_raw_sort
from src.schemas.master import ItemCreate, ItemUpdate

ALLOWED_ITEM_SORTS = {
    "ItemCode": "ItemCode",
    "ProductType": "ProductType",
    "ItemDescription": "ItemDescription",
    "ItemType": "ItemType",
    "HSNCode": "HSNCode",
    "UOM": "UOM",
    "SerialNo": "SerialNo",
    "Status": "Status",
    "CreatedOn": "CreatedOn",
}


def get_items(
    db: Session,
    search: Optional[str] = None,
    product_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    fetch_all: bool = False,
):
    query = """
        SELECT
            ItemCode,
            ProductType,
            ItemDescription,
            ItemType,
            HSNCode,
            UOM,
            SerialNo,
            Status
        FROM dbo.Mst_Item
        WHERE Status <> 'Delete'
    """

    params = {}

    if product_type and product_type != "ALL":
        query += " AND ProductType = :product_type"
        params["product_type"] = product_type

    if search and search.strip():
        query += """
            AND (
                ItemDescription LIKE :search
                OR ItemCode LIKE :search
                OR HSNCode LIKE :search
            )
        """
        params["search"] = f"%{search.strip()}%"

    sort_col, sort_dir = resolve_raw_sort(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_columns=ALLOWED_ITEM_SORTS,
        default_column="CreatedOn",
        default_order="DESC",
    )

    return paginate_raw_sql(
        db=db,
        base_query=query,
        params=params,
        page=page,
        page_size=page_size,
        sort_column=sort_col,
        sort_order=sort_dir,
        fetch_all=fetch_all,
    )


def create_item(db: Session, payload: ItemCreate):
    item_code = payload.ItemCode.strip()

    if not item_code:
        raise HTTPException(
            status_code=422,
            detail="Item code is required",
        )

    duplicate = db.execute(
        text("""
            SELECT TOP 1 ItemCode
            FROM dbo.Mst_Item
            WHERE ItemCode = :code
              AND Status <> 'Delete'
        """),
        {"code": item_code},
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="Item code already exists",
        )

    insert_sql = """
        INSERT INTO dbo.Mst_Item (
            CCode,
            LCode,
            ItemCode,
            ProductType,
            ItemDescription,
            ItemType,
            UOM,
            HSNCode,
            SerialNo,
            [Status],
            Host_IP,
            Host_Name,
            UserCode,
            UserName,
            CreatedOn
        )
        VALUES (
            'SCT',
            'UNIT I',
            :item_code,
            :product_type,
            :item_description,
            :item_type,
            :uom,
            :hsn_code,
            :serial_no,
            'Add',
            '127.0.0.1',
            'API_SERVER',
            'ADMIN',
            'Super Admin',
            GETDATE()
        )
    """

    try:
        db.execute(
            text(insert_sql),
            {
                "item_code": item_code,
                "product_type": payload.ProductType,
                "item_description": payload.ItemDescription,
                "item_type": payload.ItemType,
                "uom": payload.UOM,
                "hsn_code": payload.HSNCode,
                "serial_no": payload.SerialNo,
            },
        )
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": "Item created successfully",
        "item_code": item_code,
    }


def update_item(
    db: Session,
    item_code: str,
    payload: ItemUpdate,
):
    item_code = unquote(str(item_code or "")).strip()
    existing = db.execute(
        text("""
            SELECT TOP 1 ItemCode
            FROM dbo.Mst_Item
            WHERE (ItemCode = :item_code OR LOWER(LTRIM(RTRIM(ItemCode))) = LOWER(:item_code))
              AND Status <> 'Delete'
        """),
        {"item_code": item_code},
    ).first()

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Active item not found",
        )

    update_sql = """
        UPDATE dbo.Mst_Item
        SET
            ProductType = COALESCE(:product_type, ProductType),
            ItemDescription = COALESCE(
                :item_description, ItemDescription
            ),
            ItemType = COALESCE(:item_type, ItemType),
            HSNCode = COALESCE(:hsn_code, HSNCode),
            UOM = COALESCE(:uom, UOM),
            SerialNo = COALESCE(:serial_no, SerialNo)
        WHERE ItemCode = :item_code
          AND Status <> 'Delete'
    """

    try:
        db.execute(
            text(update_sql),
            {
                "item_code": item_code,
                "product_type": payload.ProductType,
                "item_description": payload.ItemDescription,
                "item_type": payload.ItemType,
                "hsn_code": payload.HSNCode,
                "uom": payload.UOM,
                "serial_no": payload.SerialNo,
            },
        )
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": f"Item {item_code} updated successfully",
    }


def delete_item(db: Session, item_code: str):
    item_code = unquote(str(item_code or "")).strip()
    result = db.execute(
        text("""
            UPDATE dbo.Mst_Item
            SET Status = 'Delete'
            WHERE (ItemCode = :item_code OR LOWER(LTRIM(RTRIM(ItemCode))) = LOWER(:item_code))
              AND Status <> 'Delete'
        """),
        {"item_code": item_code},
    )

    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail="Active item not found",
        )

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": f"Item {item_code} deleted successfully",
    }
