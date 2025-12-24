import re
from typing import Optional, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def detect_factory_from_filename(filename: str) -> Optional[str]:
    """
    從檔案名稱識別廠別
    支援: AMA, AMC, AMD
    """
    filename_upper = filename.upper()
    
    if "AMA" in filename_upper:
        return "AMA"
    elif "AMC" in filename_upper:
        return "AMC"
    elif "AMD" in filename_upper:
        return "AMD"
    
    return None

def detect_file_type(filename: str) -> Optional[str]:
    """
    從檔案名稱識別報表類型
    """
    filename_lower = filename.lower()
    
    if "零件出貨" in filename or "出货" in filename_lower:
        return "零件出貨"
    elif "零件銷售" in filename or "销售" in filename_lower:
        return "零件銷售"
    elif "shelf life" in filename_lower or "shelf_life" in filename_lower:
        return "Shelf Life Code"
    elif "技師績效" in filename or "技师" in filename_lower or "工资" in filename_lower:
        return "技師績效"
    elif "維修收入" in filename or "维修" in filename_lower or "收入" in filename_lower:
        return "維修收入"
    
    return None

def detect_factories_from_dataframe(df: pd.DataFrame) -> List[str]:
    """
    從 DataFrame 中偵測所有廠別 - 改進版本
    採用多層策略:
    1. 先尋找標準廠別欄位
    2. 如果找不到，掃描所有欄位尋找 AMA/AMC/AMD
    3. 如果還是找不到，檢查所有資料值（包含搜尋）
    """
    factories = set()
    
    logger.info(f"開始偵測廠別，DataFrame 欄位: {list(df.columns)}")
    
    # 第一步：尋找標準廠別欄位名稱
    factory_column_names = [
        '廠別', '工廠', '廠', '工厂', 
        'factory', 'Factory', 'FACTORY', 
        '廠商', '供應商', '供应商',
        '製造廠', '制造厂'
    ]
    
    for col in df.columns:
        if col in factory_column_names:
            logger.info(f"找到廠別欄位: {col}")
            unique_values = df[col].dropna().unique()
            for value in unique_values:
                value_str = str(value).strip().upper()
                if value_str in ['AMA', 'AMC', 'AMD']:
                    factories.add(value_str)
                    logger.info(f"從欄位 {col} 找到廠別: {value_str}")
    
    # 第二步：如果沒找到，掃描所有欄位尋找完全匹配
    if not factories:
        logger.info("未找到標準廠別欄位，掃描所有欄位...")
        for col in df.columns:
            try:
                unique_values = df[col].dropna().unique()
                for value in unique_values:
                    value_str = str(value).strip().upper()
                    if value_str in ['AMA', 'AMC', 'AMD']:
                        factories.add(value_str)
                        logger.info(f"從欄位 {col} 找到廠別: {value_str}")
            except Exception as e:
                logger.debug(f"掃描欄位 {col} 時出錯: {e}")
    
    # 第三步：如果還是沒找到，檢查所有資料值（包含搜尋）
    if not factories:
        logger.info("未找到完全匹配，進行包含搜尋...")
        for col in df.columns:
            try:
                unique_values = df[col].dropna().unique()
                for value in unique_values:
                    value_str = str(value).strip().upper()
                    # 檢查是否包含廠別代碼
                    if 'AMA' in value_str:
                        factories.add('AMA')
                        logger.info(f"從欄位 {col} 值 '{value_str}' 找到廠別: AMA")
                    if 'AMC' in value_str:
                        factories.add('AMC')
                        logger.info(f"從欄位 {col} 值 '{value_str}' 找到廠別: AMC")
                    if 'AMD' in value_str:
                        factories.add('AMD')
                        logger.info(f"從欄位 {col} 值 '{value_str}' 找到廠別: AMD")
            except Exception as e:
                logger.debug(f"掃描欄位 {col} 時出錯: {e}")
    
    logger.info(f"最終偵測到的廠別: {list(factories)}")
    return list(factories)

def get_factory_column_name(df: pd.DataFrame) -> Optional[str]:
    """
    取得 DataFrame 中廠別欄位的名稱
    """
    factory_column_names = [
        '廠別', '工廠', '廠', '工厂', 
        'factory', 'Factory', 'FACTORY', 
        '廠商', '供應商', '供应商',
        '製造廠', '制造厂'
    ]
    
    for col in df.columns:
        if col in factory_column_names:
            return col
    
    return None

def filter_dataframe_by_factory(df: pd.DataFrame, factory_code: str) -> pd.DataFrame:
    """
    根據廠別代碼篩選 DataFrame
    """
    factory_col = get_factory_column_name(df)
    
    if factory_col:
        return df[df[factory_col].astype(str).str.upper() == factory_code]
    
    # 如果沒有標準廠別欄位，返回整個 DataFrame
    return df
