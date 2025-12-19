import re
from typing import Optional

def detect_factory_from_filename(filename: str) -> Optional[str]:
    """
    從檔案名稱識別廠別
    支援: AMA, AMC, AMD
    """
    filename_upper = filename.upper()
    
    # 檢查檔名中是否包含廠別代碼
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

def validate_factory_code(factory_code: str) -> bool:
    """驗證廠別代碼是否有效"""
    return factory_code in ["AMA", "AMC", "AMD"]

