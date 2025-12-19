from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
import models
import schemas

# ==========================================
# 基礎 CRUD 操作
# ==========================================

def get_factories(db: Session) -> List[models.Factory]:
    """獲取所有廠別"""
    return db.query(models.Factory).all()

def get_factory_by_code(db: Session, code: str) -> Optional[models.Factory]:
    """根據代碼獲取廠別"""
    return db.query(models.Factory).filter(models.Factory.code == code).first()

def create_factory(db: Session, code: str, name: str) -> models.Factory:
    """創建新廠別"""
    db_factory = models.Factory(code=code, name=name)
    db.add(db_factory)
    db.commit()
    db.refresh(db_factory)
    return db_factory

# ==========================================
# 工單操作
# ==========================================

def get_or_create_work_order(db: Session, factory_code: str, order_number: str) -> models.WorkOrder:
    """獲取或創建工單"""
    work_order = db.query(models.WorkOrder).filter(
        models.WorkOrder.factory_code == factory_code,
        models.WorkOrder.order_number == order_number
    ).first()
    
    if not work_order:
        work_order = models.WorkOrder(
            factory_code=factory_code,
            order_number=order_number
        )
        db.add(work_order)
        db.commit()
        db.refresh(work_order)
    
    return work_order

# ==========================================
# 零件分類操作
# ==========================================

def get_or_create_part_category(
    db: Session, 
    part_number: str, 
    category: str = "未分類",
    shelf_life_code: Optional[str] = None,
    description: Optional[str] = None
) -> models.PartCategory:
    """獲取或創建零件分類"""
    part_cat = db.query(models.PartCategory).filter(
        models.PartCategory.part_number == part_number
    ).first()
    
    if not part_cat:
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

def update_part_category_from_shelf_life(
    db: Session,
    part_number: str,
    category: str,
    shelf_life_code: str
) -> models.PartCategory:
    """從 Shelf Life Code 更新零件分類"""
    part_cat = db.query(models.PartCategory).filter(
        models.PartCategory.part_number == part_number
    ).first()
    
    if part_cat:
        part_cat.category = category
        part_cat.shelf_life_code = shelf_life_code
    else:
        part_cat = models.PartCategory(
            part_number=part_number,
            category=category,
            shelf_life_code=shelf_life_code
        )
        db.add(part_cat)
    
    db.commit()
    db.refresh(part_cat)
    return part_cat

# ==========================================
# 檔案上傳記錄操作
# ==========================================

def check_file_exists(db: Session, file_hash: str) -> Optional[models.FileUpload]:
    """檢查檔案是否已上傳"""
    return db.query(models.FileUpload).filter(
        models.FileUpload.file_hash == file_hash
    ).first()

def create_file_upload(
    db: Session,
    file_name: str,
    file_hash: str,
    factory_code: Optional[str],
    file_type: str,
    record_count: int,
    status: str = "processed"
) -> models.FileUpload:
    """創建檔案上傳記錄"""
    file_upload = models.FileUpload(
        file_name=file_name,
        file_hash=file_hash,
        factory_code=factory_code,
        file_type=file_type,
        record_count=record_count,
        status=status
    )
    db.add(file_upload)
    db.commit()
    db.refresh(file_upload)
    return file_upload

def delete_records_by_upload_id(db: Session, upload_id: int, file_type: str):
    """根據上傳ID刪除舊記錄（用於覆蓋）"""
    upload_id_str = str(upload_id)
    
    if file_type == "零件出貨":
        db.query(models.PartShipment).filter(
            models.PartShipment.file_upload_id == upload_id_str
        ).delete()
    elif file_type == "零件銷售":
        db.query(models.PartSale).filter(
            models.PartSale.file_upload_id == upload_id_str
        ).delete()
    elif file_type == "技師績效":
        db.query(models.TechnicianPerformance).filter(
            models.TechnicianPerformance.file_upload_id == upload_id_str
        ).delete()
    elif file_type == "維修收入":
        db.query(models.MaintenanceIncome).filter(
            models.MaintenanceIncome.file_upload_id == upload_id_str
        ).delete()
    
    db.commit()

# ==========================================
# 業績查詢操作
# ==========================================

def get_factory_performance(db: Session) -> List[dict]:
    """獲取廠業績總覽"""
    query = text("""
        SELECT * FROM v_factory_performance
        ORDER BY factory_code
    """)
    result = db.execute(query)
    return [dict(row._mapping) for row in result]

def get_technician_performance_summary(db: Session, factory_code: Optional[str] = None) -> List[dict]:
    """獲取技師績效總覽"""
    if factory_code:
        query = text("""
            SELECT * FROM v_technician_performance_summary
            WHERE factory_code = :factory_code
            ORDER BY total_income DESC
        """)
        result = db.execute(query, {"factory_code": factory_code})
    else:
        query = text("""
            SELECT * FROM v_technician_performance_summary
            ORDER BY total_income DESC
        """)
        result = db.execute(query)
    
    return [dict(row._mapping) for row in result]

def get_part_sales_summary(db: Session, category: Optional[str] = None) -> List[dict]:
    """獲取零件銷售統計"""
    if category:
        query = text("""
            SELECT * FROM v_part_sales_summary
            WHERE category = :category
            ORDER BY total_amount DESC
        """)
        result = db.execute(query, {"category": category})
    else:
        query = text("""
            SELECT * FROM v_part_sales_summary
            ORDER BY total_amount DESC
        """)
        result = db.execute(query)
    
    return [dict(row._mapping) for row in result]

# ==========================================
# 批量插入操作
# ==========================================

def bulk_insert_part_shipments(db: Session, shipments: List[models.PartShipment]):
    """批量插入零件出貨記錄"""
    db.bulk_save_objects(shipments)
    db.commit()

def bulk_insert_part_sales(db: Session, sales: List[models.PartSale]):
    """批量插入零件銷售記錄"""
    db.bulk_save_objects(sales)
    db.commit()

def bulk_insert_technician_performance(db: Session, performances: List[models.TechnicianPerformance]):
    """批量插入技師績效記錄"""
    db.bulk_save_objects(performances)
    db.commit()

def bulk_insert_maintenance_income(db: Session, incomes: List[models.MaintenanceIncome]):
    """批量插入維修收入記錄"""
    db.bulk_save_objects(incomes)
    db.commit()

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
