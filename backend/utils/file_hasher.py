import hashlib
from typing import BinaryIO

def calculate_file_hash(file: BinaryIO) -> str:
    """
    計算檔案的 SHA256 雜湊值
    用於檢測重複上傳
    """
    sha256_hash = hashlib.sha256()
    
    # 重置檔案指針到開頭
    file.seek(0)
    
    # 分塊讀取檔案計算雜湊
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    
    # 重置檔案指針到開頭，供後續使用
    file.seek(0)
    
    return sha256_hash.hexdigest()

