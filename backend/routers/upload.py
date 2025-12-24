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
    get_factory_column_name
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
            
            # 識別報表類型
            file_type = detect_file_type(file.filename)
            
            # 解析 Excel
            parser = ExcelParser()
            df = parser.read_excel(content)
            
            # 嘗試從檔案名稱識別廠別
            factory_code = detect_factory_from_filename(file.filename)
            
            # 如果檔案名稱中沒有廠別，從 Excel 資料中偵測
            if not factory_code:
                factories = detect_factories_from_dataframe(df)
                if not factories:
                    raise HTTPException(
                        status_code=400,
                        detail=f"無法從檔案名稱或資料中識別廠別: {file.filename}"
                    )
                # 如果有多個廠別，需要分別處理
                if len(factories) > 1:
                    # 多廠別情況：為每個廠別分別建立記錄
                    factory_column = get_factory_column_name(df)
                    for factory in factories:
                        await process_factory_data(
                            db, df, file, file_type, factory, factory_column, file_hash, results
                        )
                    continue
                else:
                    factory_code = factories[0]
            
            # 根據報表類型處理
            record_count = 0
            
            if file_type == "Shelf Life Code":
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
            logger.info(f"成功處理檔案: {file.filename}, 廠別: {factory_code}, 記錄數: {record_count}")
            
        except Exception as e:
            logger.error(f"處理檔案 {file.filename} 時發生錯誤: {str(e)}")
            raise HTTPException(status_code=500, detail=f"處理檔案失敗: {str(e)}")
    
    return results

async def process_factory_data(db, df, file, file_type, factory_code, factory_column, file_hash, results):
    """
    處理特定廠別的資料
    """
    try:
        # 過濾該廠別的資料
        factory_df = df[df[factory_column].str.upper() == factory_code].copy()
        
        if factory_df.empty:
            logger.warning(f"廠別 {factory_code} 的資料為空")
            return
        
        parser = ExcelParser()
        record_count = 0
        
        if file_type == "零件出貨":
            records = parser.parse_part_shipment(factory_df, factory_code)
            for record in records:
                crud.create_part_shipment(db, factory_code, record)
            record_count = len(records)
            
        elif file_type == "零件銷售":
            records = parser.parse_part_sales(factory_df, factory_code)
            for record in records:
                crud.create_part_sale(db, factory_code, record)
            record_count = len(records)
            
        elif file_type == "技師績效":
            records = parser.parse_technician_performance(factory_df, factory_code)
            for record in records:
                crud.create_technician_performance(db, factory_code, record)
            record_count = len(records)
            
        elif file_type == "維修收入":
            records = parser.parse_maintenance_income(factory_df, factory_code)
            for record in records:
                crud.create_maintenance_income(db, factory_code, record)
            record_count = len(records)
        
        # 記錄上傳資訊
        file_upload = crud.create_file_upload(
            db,
            file_name=f"{file.filename} ({factory_code})",
            file_hash=file_hash,
            factory_code=factory_code,
            file_type=file_type,
            record_count=record_count
        )
        
        results.append(file_upload)
        logger.info(f"成功處理廠別 {factory_code}: {file.filename}, 記錄數: {record_count}")
        
    except Exception as e:
        logger.error(f"處理廠別 {factory_code} 時發生錯誤: {str(e)}")
        raise
