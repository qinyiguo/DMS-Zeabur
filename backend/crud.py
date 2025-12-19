from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
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

