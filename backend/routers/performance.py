from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from database import get_db
import crud
import schemas

router = APIRouter()

@router.get("/factory", response_model=List[schemas.FactoryPerformance])
def get_factory_performance(
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    查詢廠別業績
    - 總工單數
    - 總收入
    - 零件銷售
    - 零件出貨
    - 人工成本
    - 淨利潤
    """
    return crud.calculate_factory_performance(
        db,
        factory_code=factory_code,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/technician", response_model=List[schemas.TechnicianPerformanceSummary])
def get_technician_performance(
    factory_code: Optional[str] = None,
    technician_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    查詢技師個人業績
    - 完成工單數
    - 總工時
    - 總工資
    - 平均時薪
    """
    return crud.calculate_technician_performance(
        db,
        factory_code=factory_code,
        technician_name=technician_name,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/summary")
def get_performance_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    綜合業績摘要
    - 所有廠別總計
    - 各廠別對比
    - 趨勢分析
    """
    factories = crud.calculate_factory_performance(
        db,
        start_date=start_date,
        end_date=end_date
    )
    
    total_income = sum(f.total_income for f in factories)
    total_orders = sum(f.total_orders for f in factories)
    total_profit = sum(f.net_profit for f in factories)
    
    return {
        "summary": {
            "total_income": total_income,
            "total_orders": total_orders,
            "total_profit": total_profit,
            "factory_count": len(factories)
        },
        "factories": factories
    }

@router.get("/part-category-analysis")
def get_part_category_analysis(
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    零件分類分析
    - 零件 vs 配件 vs 精品 的銷售佔比
    """
    return crud.analyze_part_categories(
        db,
        factory_code=factory_code,
        start_date=start_date,
        end_date=end_date
    )

