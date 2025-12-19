from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from database import get_db
import crud
import schemas

router = APIRouter()

@router.get("/part-shipments")
def get_part_shipments(
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """查詢零件出貨記錄"""
    return crud.get_part_shipments(
        db,
        factory_code=factory_code,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

@router.get("/part-sales")
def get_part_sales(
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """查詢零件銷售記錄"""
    return crud.get_part_sales(
        db,
        factory_code=factory_code,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

@router.get("/maintenance-income")
def get_maintenance_income(
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """查詢維修收入記錄"""
    return crud.get_maintenance_income(
        db,
        factory_code=factory_code,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

@router.get("/work-orders/{factory_code}/{order_number}")
def get_work_order_detail(
    factory_code: str,
    order_number: str,
    db: Session = Depends(get_db)
):
    """查詢工單詳細資訊（包含所有關聯資料）"""
    return crud.get_work_order_with_details(db, factory_code, order_number)

