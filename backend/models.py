from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Factory(Base):
    __tablename__ = "factories"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    work_orders = relationship("WorkOrder", back_populates="factory")

class WorkOrder(Base):
    __tablename__ = "work_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    factory_code = Column(String(10), ForeignKey("factories.code"), nullable=False)
    order_number = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    factory = relationship("Factory", back_populates="work_orders")
    part_shipments = relationship("PartShipment", back_populates="work_order")
    part_sales = relationship("PartSale", back_populates="work_order")
    technician_performances = relationship("TechnicianPerformance", back_populates="work_order")
    maintenance_incomes = relationship("MaintenanceIncome", back_populates="work_order")

class PartCategory(Base):
    __tablename__ = "part_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String(50), unique=True, nullable=False, index=True)
    category = Column(String(20), nullable=False)
    shelf_life_code = Column(String(50))
    description = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    part_shipments = relationship("PartShipment", back_populates="part_category")
    part_sales = relationship("PartSale", back_populates="part_category")

class PartShipment(Base):
    __tablename__ = "part_shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    factory_code = Column(String(10), nullable=False)
    order_number = Column(String(50), nullable=False)
    part_number = Column(String(50), ForeignKey("part_categories.part_number"))
    quantity = Column(Integer, default=0)
    amount = Column(Numeric(12, 2), default=0)
    shipment_date = Column(Date)
    file_upload_id = Column(String(100))
    row_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    work_order = relationship("WorkOrder", back_populates="part_shipments")
    part_category = relationship("PartCategory", back_populates="part_shipments")

class PartSale(Base):
    __tablename__ = "part_sales"
    
    id = Column(Integer, primary_key=True, index=True)
    factory_code = Column(String(10), nullable=False)
    order_number = Column(String(50), nullable=False)
    part_number = Column(String(50), ForeignKey("part_categories.part_number"))
    quantity = Column(Integer, default=0)
    amount = Column(Numeric(12, 2), default=0)
    sale_date = Column(Date)
    file_upload_id = Column(String(100))
    row_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    work_order = relationship("WorkOrder", back_populates="part_sales")
    part_category = relationship("PartCategory", back_populates="part_sales")

class TechnicianPerformance(Base):
    __tablename__ = "technician_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    factory_code = Column(String(10), nullable=False)
    order_number = Column(String(50))
    technician_name = Column(String(100), nullable=False)
    work_hours = Column(Numeric(8, 2), default=0)
    salary = Column(Numeric(12, 2), default=0)
    bonus = Column(Numeric(12, 2), default=0)
    performance_date = Column(Date)
    file_upload_id = Column(String(100))
    row_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    work_order = relationship("WorkOrder", back_populates="technician_performances")

class MaintenanceIncome(Base):
    __tablename__ = "maintenance_income"
    
    id = Column(Integer, primary_key=True, index=True)
    factory_code = Column(String(10), nullable=False)
    order_number = Column(String(50), nullable=False)
    income_category = Column(String(100))
    amount = Column(Numeric(12, 2), default=0)
    income_date = Column(Date)
    file_upload_id = Column(String(100))
    row_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    work_order = relationship("WorkOrder", back_populates="maintenance_incomes")

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    factory_code = Column(String(10))
    file_type = Column(String(50))
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    record_count = Column(Integer, default=0)
    status = Column(String(20), default="processed")
    error_message = Column(Text)
    uploaded_by = Column(String(100))

