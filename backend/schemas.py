from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# 基礎 Schema
class FactoryBase(BaseModel):
    code: str
    name: str

class Factory(FactoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 檔案上傳相關
class FileUploadResponse(BaseModel):
    id: int
    file_name: str
    file_hash: str
    factory_code: Optional[str]
    file_type: Optional[str]
    record_count: int
    status: str
    upload_date: datetime
    
    class Config:
        from_attributes = True

# 業績相關
class FactoryPerformance(BaseModel):
    factory_code: str
    factory_name: str
    total_orders: int
    total_income: Decimal
    parts_sales: Decimal
    parts_shipments: Decimal
    total_labor_cost: Decimal
    net_profit: Decimal

class TechnicianPerformanceSummary(BaseModel):
    technician_name: str
    factory_code: str
    factory_name: Optional[str]
    total_orders: int
    total_hours: Decimal
    total_salary: Decimal
    total_bonus: Decimal
    total_income: Decimal
    avg_hourly_rate: Decimal

class PartSalesSummary(BaseModel):
    part_number: str
    category: Optional[str]
    description: Optional[str]
    transaction_count: int
    total_quantity: int
    total_amount: Decimal
    avg_amount: Decimal

# 上傳結果
class UploadResult(BaseModel):
    success: bool
    message: str
    file_upload_id: Optional[int]
    factory_code: Optional[str]
    file_type: str
    record_count: int
    duplicate: bool = False
    action_taken: str  # "inserted", "skipped", "overwritten"

