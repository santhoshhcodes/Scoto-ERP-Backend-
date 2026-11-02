
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.schemas.master import ItemCreate, ItemUpdate


def get_items(
    db: Session,
    search: str | None = None,
    product_type: str | None = None,
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

    query += " ORDER BY CreatedOn DESC"

    result = db.execute(
        text(query),
        params,
    ).mappings().all()

    return {
        "success": True,
        "count": len(result),
        "data": [dict(row) for row in result],
    }


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
            '01',
            '01',
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
    existing = db.execute(
        text("""
            SELECT TOP 1 ItemCode
            FROM dbo.Mst_Item
            WHERE ItemCode = :item_code
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
    result = db.execute(
        text("""
            UPDATE dbo.Mst_Item
            SET Status = 'Delete'
            WHERE ItemCode = :item_code
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
