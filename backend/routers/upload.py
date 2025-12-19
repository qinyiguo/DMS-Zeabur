from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import crud
import schemas
from utils.excel_parser import ExcelParser
from utils.factory_detector import detect_factory_from_filename, detect_file_type
from utils.file_hasher import calculate_file_hash
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/excel", response_model=List[schemas.FileUploadResponse])
async def upload_excel_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    上傳多個 Excel 報表
    - 自動識別廠別 (AMA/AMC/AMD)
    - 自動識別報表類型
    - 防止重複上傳
    """
    results = []
    
    for file in files:
        try:
            # 讀取檔案內容
            content = await file.read()
            file_hash = calculate_file_hash(content)
            
            # 檢查是否已上傳過
            existing_file = crud.get_file_by_hash(db, file_hash)
            if existing_file:
                logger.info(f"檔案 {file.filename} 已存在，跳過")
                results.append(existing_file)
                continue
            
            # 識別廠別和報表類型
            factory_code = detect_factory_from_filename(file.filename)
            file_type = detect_file_type(file.filename)
            
            # 解析 Excel
            parser = ExcelParser()
            df = parser.read_excel(content)
            
            # 根據報表類型處理
            record_count = 0
            
            if file_type == "Shelf Life Code":
                # 先處理 Shelf Life Code（用於零件分類）
                records = parser.parse_shelf_life_code(df)
                for record in records:
                    crud.create_or_update_part_category(
                        db,
                        part_number=record['part_number'],
                        category=record['category'],
                        shelf_life_code=record.get('shelf_life_code'),
                        description=record.get('description')
                    )
                record_count = len(records)
                
            elif file_type == "零件出貨" and factory_code:
                records = parser.parse_part_shipment(df, factory_code)
                for record in records:
                    crud.create_part_shipment(db, factory_code, record)
                record_count = len(records)
                
            elif file_type == "零件銷售" and factory_code:
                records = parser.parse_part_sales(df, factory_code)
                for record in records:
                    crud.create_part_sale(db, factory_code, record)
                record_count = len(records)
                
            elif file_type == "技師績效" and factory_code:
                records = parser.parse_technician_performance(df, factory_code)
                for record in records:
                    crud.create_technician_performance(db, factory_code, record)
                record_count = len(records)
                
            elif file_type == "維修收入" and factory_code:
                records = parser.parse_maintenance_income(df, factory_code)
                for record in records:
                    crud.create_maintenance_income(db, factory_code, record)
                record_count = len(records)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"無法識別報表類型或廠別: {file.filename}"
                )
            
            # 記錄上傳資訊
            file_upload = crud.create_file_upload(
                db,
                file_name=file.filename,
                file_hash=file_hash,
                factory_code=factory_code,
                file_type=file_type,
                record_count=record_count
            )
            
            results.append(file_upload)
            logger.info(f"成功處理檔案: {file.filename}, 記錄數: {record_count}")
            
        except Exception as e:
            logger.error(f"處理檔案 {file.filename} 時發生錯誤: {str(e)}")
            raise HTTPException(status_code=500, detail=f"處理檔案失敗: {str(e)}")
    
    return results

@router.get("/history", response_model=List[schemas.FileUploadResponse])
def get_upload_history(
    factory_code: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """查詢上傳歷史"""
    return crud.get_file_uploads(db, factory_code=factory_code, limit=limit)

# 在 crud.py 末尾添加

def get_file_by_hash(db: Session, file_hash: str) -> Optional[models.FileUpload]:
    """根據檔案雜湊值查詢上傳記錄"""
    return db.query(models.FileUpload).filter(
        models.FileUpload.file_hash == file_hash
    ).first()

def get_file_uploads(
    db: Session, 
    factory_code: Optional[str] = None, 
    limit: int = 50
) -> List[models.FileUpload]:
    """查詢上傳歷史"""
    query = db.query(models.FileUpload)
    
    if factory_code:
        query = query.filter(models.FileUpload.factory_code == factory_code)
    
    return query.order_by(models.FileUpload.upload_date.desc()).limit(limit).all()

def create_or_update_part_category(
    db: Session,
    part_number: str,
    category: str,
    shelf_life_code: Optional[str] = None,
    description: Optional[str] = None
) -> models.PartCategory:
    """創建或更新零件分類"""
    part_cat = db.query(models.PartCategory).filter(
        models.PartCategory.part_number == part_number
    ).first()
    
    if part_cat:
        # 更新現有記錄
        part_cat.category = category
        if shelf_life_code:
            part_cat.shelf_life_code = shelf_life_code
        if description:
            part_cat.description = description
        part_cat.updated_at = func.now()
    else:
        # 創建新記錄
        part_cat = models.PartCategory(
            part_number=part_number,
            category=category,
            shelf_life_code=shelf_life_code,
            description=description
        )
        db.add(part_cat)
    
    db.commit()
    db.refresh(part_cat)
    return part_cat

def create_part_shipment(db: Session, factory_code: str, record: dict) -> models.PartShipment:
    """創建零件出貨記錄"""
    # 確保工單存在
    work_order = get_or_create_work_order(db, factory_code, record['order_number'])
    
    # 確保零件分類存在
    get_or_create_part_category(db, record['part_number'])
    
    shipment = models.PartShipment(
        factory_code=factory_code,
        order_number=record['order_number'],
        part_number=record['part_number'],
        quantity=record.get('quantity', 0),
        amount=record.get('amount', 0),
        shipment_date=record.get('shipment_date'),
        row_data=record.get('row_data')
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment

def create_part_sale(db: Session, factory_code: str, record: dict) -> models.PartSale:
    """創建零件銷售記錄"""
    work_order = get_or_create_work_order(db, factory_code, record['order_number'])
    get_or_create_part_category(db, record['part_number'])
    
    sale = models.PartSale(
        factory_code=factory_code,
        order_number=record['order_number'],
        part_number=record['part_number'],
        quantity=record.get('quantity', 0),
        amount=record.get('amount', 0),
        sale_date=record.get('sale_date'),
        row_data=record.get('row_data')
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale

def create_technician_performance(db: Session, factory_code: str, record: dict) -> models.TechnicianPerformance:
    """創建技師績效記錄"""
    if record.get('order_number'):
        work_order = get_or_create_work_order(db, factory_code, record['order_number'])
    
    performance = models.TechnicianPerformance(
        factory_code=factory_code,
        order_number=record.get('order_number'),
        technician_name=record['technician_name'],
        work_hours=record.get('work_hours', 0),
        salary=record.get('salary', 0),
        bonus=record.get('bonus', 0),
        performance_date=record.get('performance_date'),
        row_data=record.get('row_data')
    )
    db.add(performance)
    db.commit()
    db.refresh(performance)
    return performance

def create_maintenance_income(db: Session, factory_code: str, record: dict) -> models.MaintenanceIncome:
    """創建維修收入記錄"""
    work_order = get_or_create_work_order(db, factory_code, record['order_number'])
    
    income = models.MaintenanceIncome(
        factory_code=factory_code,
        order_number=record['order_number'],
        income_category=record.get('income_category'),
        amount=record.get('amount', 0),
        income_date=record.get('income_date'),
        row_data=record.get('row_data')
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return income

def calculate_factory_performance(
    db: Session,
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[dict]:
    """計算廠別業績"""
    # 這裡使用 SQL View 或直接查詢
    return get_factory_performance(db)

def calculate_technician_performance(
    db: Session,
    factory_code: Optional[str] = None,
    technician_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[dict]:
    """計算技師業績"""
    return get_technician_performance_summary(db, factory_code)

def analyze_part_categories(
    db: Session,
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> dict:
    """分析零件分類銷售"""
    query = db.query(
        models.PartCategory.category,
        func.count(models.PartSale.id).label('count'),
        func.sum(models.PartSale.amount).label('total_amount')
    ).join(
        models.PartSale,
        models.PartCategory.part_number == models.PartSale.part_number
    )
    
    if factory_code:
        query = query.filter(models.PartSale.factory_code == factory_code)
    
    if start_date:
        query = query.filter(models.PartSale.sale_date >= start_date)
    
    if end_date:
        query = query.filter(models.PartSale.sale_date <= end_date)
    
    result = query.group_by(models.PartCategory.category).all()
    
    return {
        'categories': [
            {
                'category': row.category,
                'count': row.count,
                'total_amount': float(row.total_amount or 0)
            }
            for row in result
        ]
    }

def get_part_shipments(
    db: Session,
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100
):
    """查詢零件出貨記錄"""
    query = db.query(models.PartShipment)
    
    if factory_code:
        query = query.filter(models.PartShipment.factory_code == factory_code)
    
    if start_date:
        query = query.filter(models.PartShipment.shipment_date >= start_date)
    
    if end_date:
        query = query.filter(models.PartShipment.shipment_date <= end_date)
    
    return query.order_by(models.PartShipment.shipment_date.desc()).limit(limit).all()

def get_part_sales(
    db: Session,
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100
):
    """查詢零件銷售記錄"""
    query = db.query(models.PartSale)
    
    if factory_code:
        query = query.filter(models.PartSale.factory_code == factory_code)
    
    if start_date:
        query = query.filter(models.PartSale.sale_date >= start_date)
    
    if end_date:
        query = query.filter(models.PartSale.sale_date <= end_date)
    
    return query.order_by(models.PartSale.sale_date.desc()).limit(limit).all()

def get_maintenance_income(
    db: Session,
    factory_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100
):
    """查詢維修收入記錄"""
    query = db.query(models.MaintenanceIncome)
    
    if factory_code:
        query = query.filter(models.MaintenanceIncome.factory_code == factory_code)
    
    if start_date:
        query = query.filter(models.MaintenanceIncome.income_date >= start_date)
    
    if end_date:
        query = query.filter(models.MaintenanceIncome.income_date <= end_date)
    
    return query.order_by(models.MaintenanceIncome.income_date.desc()).limit(limit).all()

def get_work_order_with_details(db: Session, factory_code: str, order_number: str):
    """查詢工單詳細資訊"""
    work_order = db.query(models.WorkOrder).filter(
        models.WorkOrder.factory_code == factory_code,
        models.WorkOrder.order_number == order_number
    ).first()
    
    if not work_order:
        return None
    
    return {
        'work_order': work_order,
        'part_shipments': work_order.part_shipments,
        'part_sales': work_order.part_sales,
        'technician_performances': work_order.technician_performances,
        'maintenance_incomes': work_order.maintenance_incomes
    }


