from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import crud
import schemas
from utils.excel_parser import ExcelParser
from utils.factory_detector import (
    detect_factory_from_filename, 
    detect_file_type,
    detect_factories_from_dataframe,
    get_factory_column_name,
    filter_dataframe_by_factory
)
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
    - 自動從檔案名稱識別廠別（如果有）
    - 自動從 Excel 資料中識別廠別
    - 自動識別報表類型
    - 防止重複上傳
    - 支援多廠別資料
    """
    results = []
    
    for file in files:
        try:
            logger.info(f"開始處理檔案: {file.filename}")
            
            # 讀取檔案內容
            content = await file.read()
            file_hash = calculate_file_hash(content)
            
            # 檢查是否已上傳過
            existing_file = crud.get_file_by_hash(db, file_hash)
            if existing_file:
                logger.info(f"檔案 {file.filename} 已存在，跳過")
                results.append(existing_file)
                continue
            
            # 識別報表類型
            file_type = detect_file_type(file.filename)
            logger.info(f"識別的報表類型: {file_type}")
            
            # 解析 Excel
            parser = ExcelParser()
            df = parser.read_excel(content)
            logger.info(f"Excel 檔案讀取成功，共 {len(df)} 行資料")
            
            # 嘗試從檔案名稱識別廠別
            factory_code = detect_factory_from_filename(file.filename)
            
            # 如果檔案名稱中沒有廠別，從 Excel 資料中偵測
            if not factory_code:
                factories = detect_factories_from_dataframe(df)
                if not factories:
                    error_msg = f"無法從檔案名稱或資料中識別廠別: {file.filename}"
                    logger.error(error_msg)
                    raise HTTPException(
                        status_code=400,
                        detail=error_msg
                    )
                
                logger.info(f"從資料中偵測到廠別: {factories}")
                
                # 如果有多個廠別，需要分別處理
                if len(factories) > 1:
                    logger.info(f"檔案包含多個廠別: {factories}，將分別處理")
                    for factory in factories:
                        result = await process_single_factory(
                            file, content, file_hash, df, factory, file_type, db
                        )
                        results.append(result)
                else:
                    factory_code = factories[0]
                    result = await process_single_factory(
                        file, content, file_hash, df, factory_code, file_type, db
                    )
                    results.append(result)
            else:
                logger.info(f"從檔案名稱識別到廠別: {factory_code}")
                result = await process_single_factory(
                    file, content, file_hash, df, factory_code, file_type, db
                )
                results.append(result)
        
        except HTTPException as e:
            logger.error(f"HTTP 錯誤: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"處理檔案 {file.filename} 時發生錯誤: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"處理檔案 {file.filename} 時發生錯誤: {str(e)}"
            )
    
    return results


async def process_single_factory(
    file: UploadFile,
    content: bytes,
    file_hash: str,
    df,
    factory_code: str,
    file_type: str,
    db: Session
) -> schemas.FileUploadResponse:
    """
    處理單一廠別的資料
    """
    logger.info(f"開始處理廠別 {factory_code} 的資料")
    
    # 如果有多個廠別，篩選該廠別的資料
    factory_df = filter_dataframe_by_factory(df, factory_code)
    
    if len(factory_df) == 0:
        logger.warning(f"廠別 {factory_code} 沒有資料")
        factory_df = df  # 如果篩選後沒有資料，使用全部資料
    
    logger.info(f"廠別 {factory_code} 的資料行數: {len(factory_df)}")
    
    # 確保廠別存在
    factory = crud.get_factory_by_code(db, factory_code)
    if not factory:
        logger.info(f"廠別 {factory_code} 不存在，創建新廠別")
        factory = crud.create_factory(db, factory_code, factory_code)
    
    # 根據報表類型處理資料
    record_count = 0
    
    try:
        if file_type == "零件出貨":
            record_count = await process_part_shipment(factory_df, factory_code, db)
        elif file_type == "零件銷售":
            record_count = await process_part_sales(factory_df, factory_code, db)
        elif file_type == "Shelf Life Code":
            record_count = await process_shelf_life(factory_df, db)
        elif file_type == "技師績效":
            record_count = await process_technician_performance(factory_df, factory_code, db)
        elif file_type == "維修收入":
            record_count = await process_maintenance_income(factory_df, factory_code, db)
        else:
            logger.warning(f"未知的報表類型: {file_type}")
            record_count = 0
        
        logger.info(f"成功處理 {record_count} 筆記錄")
        
    except Exception as e:
        logger.error(f"處理 {file_type} 資料時出錯: {str(e)}", exc_info=True)
        raise
    
    # 建立檔案上傳記錄
    file_upload = crud.create_file_upload(
        db,
        file_name=file.filename,
        file_hash=file_hash,
        factory_code=factory_code,
        file_type=file_type,
        record_count=record_count
    )
    
    logger.info(f"檔案上傳記錄已建立: {file_upload.id}")
    
    return file_upload


async def process_part_shipment(df, factory_code: str, db: Session) -> int:
    """處理零件出貨資料"""
    logger.info(f"開始處理零件出貨資料，廠別: {factory_code}")
    
    parser = ExcelParser()
    records = parser.parse_part_shipment(df, factory_code)
    
    count = 0
    for record in records:
        try:
            # 獲取或創建工單
            work_order = crud.get_or_create_work_order(
                db, factory_code, record['order_number']
            )
            
            # 獲取或創建零件分類
            part_category = crud.get_or_create_part_category(
                db, record['part_number']
            )
            
            # 創建零件出貨記錄
            crud.create_part_shipment(
                db,
                work_order_id=work_order.id,
                part_category_id=part_category.id,
                quantity=record['quantity'],
                amount=record['amount'],
                shipment_date=record.get('shipment_date')
            )
            count += 1
        except Exception as e:
            logger.error(f"處理零件出貨記錄時出錯: {str(e)}")
            continue
    
    logger.info(f"零件出貨資料處理完成，共 {count} 筆")
    return count


async def process_part_sales(df, factory_code: str, db: Session) -> int:
    """處理零件銷售資料"""
    logger.info(f"開始處理零件銷售資料，廠別: {factory_code}")
    
    parser = ExcelParser()
    records = parser.parse_part_sales(df, factory_code)
    
    count = 0
    for record in records:
        try:
            # 獲取或創建工單
            work_order = crud.get_or_create_work_order(
                db, factory_code, record['order_number']
            )
            
            # 獲取或創建零件分類
            part_category = crud.get_or_create_part_category(
                db, record['part_number']
            )
            
            # 創建零件銷售記錄
            crud.create_part_sale(
                db,
                work_order_id=work_order.id,
                part_category_id=part_category.id,
                quantity=record['quantity'],
                amount=record['amount'],
                sale_date=record.get('sale_date')
            )
            count += 1
        except Exception as e:
            logger.error(f"處理零件銷售記錄時出錯: {str(e)}")
            continue
    
    logger.info(f"零件銷售資料處理完成，共 {count} 筆")
    return count


async def process_shelf_life(df, db: Session) -> int:
    """處理 Shelf Life Code 資料"""
    logger.info("開始處理 Shelf Life Code 資料")
    
    parser = ExcelParser()
    records = parser.parse_shelf_life(df)
    
    count = 0
    for record in records:
        try:
            crud.update_part_shelf_life(
                db,
                part_number=record['part_number'],
                shelf_life_code=record['shelf_life_code']
            )
            count += 1
        except Exception as e:
            logger.error(f"處理 Shelf Life 記錄時出錯: {str(e)}")
            continue
    
    logger.info(f"Shelf Life Code 資料處理完成，共 {count} 筆")
    return count


async def process_technician_performance(df, factory_code: str, db: Session) -> int:
    """處理技師績效資料"""
    logger.info(f"開始處理技師績效資料，廠別: {factory_code}")
    
    parser = ExcelParser()
    records = parser.parse_technician_performance(df, factory_code)
    
    count = 0
    for record in records:
        try:
            # 獲取或創建工單
            work_order = crud.get_or_create_work_order(
                db, factory_code, record['order_number']
            )
            
            # 創建技師績效記錄
            crud.create_technician_performance(
                db,
                work_order_id=work_order.id,
                technician_name=record['technician_name'],
                hours=record['hours'],
                hourly_rate=record['hourly_rate'],
                bonus=record.get('bonus', 0)
            )
            count += 1
        except Exception as e:
            logger.error(f"處理技師績效記錄時出錯: {str(e)}")
            continue
    
    logger.info(f"技師績效資料處理完成，共 {count} 筆")
    return count


async def process_maintenance_income(df, factory_code: str, db: Session) -> int:
    """處理維修收入資料"""
    logger.info(f"開始處理維修收入資料，廠別: {factory_code}")
    
    parser = ExcelParser()
    records = parser.parse_maintenance_income(df, factory_code)
    
    count = 0
    for record in records:
        try:
            # 獲取或創建工單
            work_order = crud.get_or_create_work_order(
                db, factory_code, record['order_number']
            )
            
            # 創建維修收入記錄
            crud.create_maintenance_income(
                db,
                work_order_id=work_order.id,
                category=record['category'],
                amount=record['amount'],
                income_date=record.get('income_date')
            )
            count += 1
        except Exception as e:
            logger.error(f"處理維修收入記錄時出錯: {str(e)}")
            continue
    
    logger.info(f"維修收入資料處理完成，共 {count} 筆")
    return count
