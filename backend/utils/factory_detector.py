import re
from typing import Optional, List
import pandas as pd

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
    從 DataFrame 中偵測所有廠別
    尋找常見的廠別欄位名稱
    """
    factories = set()
    
    # 常見的廠別欄位名稱
    factory_column_names = ['廠別', '工廠', '廠', '工厂', 'factory', 'Factory', 'FACTORY']
    
    for col in df.columns:
        if col in factory_column_names:
            # 取得該欄位中的所有唯一值
            unique_values = df[col].dropna().unique()
            for value in unique_values:
                value_str = str(value).strip().upper()
                if value_str in ['AMA', 'AMC', 'AMD']:
                    factories.add(value_str)
    
    return list(factories)

def get_factory_column_name(df: pd.DataFrame) -> Optional[str]:
    """
    取得 DataFrame 中廠別欄位的名稱
    """
    factory_column_names = ['廠別', '工廠', '廠', '工厂', 'factory', 'Factory', 'FACTORY']
    
    for col in df.columns:
        if col in factory_column_names:
            return col
    
    return None
