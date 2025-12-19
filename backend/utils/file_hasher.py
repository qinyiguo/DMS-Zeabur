import hashlib

def calculate_file_hash(content: bytes) -> str:
    """
    計算檔案的 SHA256 雜湊值
    用於檢測重複上傳
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()
