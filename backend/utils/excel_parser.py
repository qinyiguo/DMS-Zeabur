import pandas as pd
from typing import Dict, List, Optional, Tuple
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class ExcelParser:
    """Excel 檔案解析器"""
    
    @staticmethod
    def read_excel(file_content: bytes, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """讀取 Excel 檔案"""
        try:
            # 支援 .xlsx 和 .xls 格式
            df = pd.read_excel(BytesIO(file_content), sheet_name=sheet_name or 0 )
            return df
        except Exception as e:
            logger.error(f"讀取 Excel 檔案失敗: {str(e)}")
            raise ValueError(f"無法讀取 Excel 檔案: {str(e)}")
    
    @staticmethod
    def parse_part_shipment(df: pd.DataFrame, factory_code: str) -> List[Dict]:
        """
        解析零件出貨報表
        預期欄位: 工單號, 零件編號, 數量, 金額, 出貨日期
        """
        records = []
        
        # 標準化欄位名稱（移除空格、統一大小寫）
        df.columns = df.columns.str.strip()
        
        # 常見的欄位名稱映射
        column_mapping = {
            '工單號': 'order_number',
            '工单号': 'order_number',
            '工單': 'order_number',
            '零件編號': 'part_number',
            '零件编号': 'part_number',
            '料號': 'part_number',
            '數量': 'quantity',
            '数量': 'quantity',
            '金額': 'amount',
            '金额': 'amount',
            '出貨日期': 'shipment_date',
            '出货日期': 'shipment_date',
            '日期': 'shipment_date'
        }
        
        # 重命名欄位
        df = df.rename(columns=column_mapping)
        
        for idx, row in df.iterrows():
            try:
                record = {
                    'factory_code': factory_code,
                    'order_number': str(row.get('order_number', '')).strip(),
                    'part_number': str(row.get('part_number', '')).strip(),
                    'quantity': int(row.get('quantity', 0)) if pd.notna(row.get('quantity')) else 0,
                    'amount': float(row.get('amount', 0)) if pd.notna(row.get('amount')) else 0,
                    'shipment_date': pd.to_datetime(row.get('shipment_date')) if pd.notna(row.get('shipment_date')) else None,
                    'row_data': row.to_dict()
                }
                
                # 跳過空記錄
                if record['order_number'] and record['part_number']:
                    records.append(record)
            except Exception as e:
                logger.warning(f"解析第 {idx+1} 行時發生錯誤: {str(e)}")
                continue
        
        return records
    
    @staticmethod
    def parse_part_sales(df: pd.DataFrame, factory_code: str) -> List[Dict]:
        """
        解析零件銷售報表
        預期欄位: 工單號, 零件編號, 數量, 金額, 銷售日期
        """
        records = []
        df.columns = df.columns.str.strip()
        
        column_mapping = {
            '工單號': 'order_number',
            '工单号': 'order_number',
            '工單': 'order_number',
            '零件編號': 'part_number',
            '零件编号': 'part_number',
            '料號': 'part_number',
            '數量': 'quantity',
            '数量': 'quantity',
            '金額': 'amount',
            '金额': 'amount',
            '銷售日期': 'sale_date',
            '销售日期': 'sale_date',
            '日期': 'sale_date'
        }
        
        df = df.rename(columns=column_mapping)
        
        for idx, row in df.iterrows():
            try:
                record = {
                    'factory_code': factory_code,
                    'order_number': str(row.get('order_number', '')).strip(),
                    'part_number': str(row.get('part_number', '')).strip(),
                    'quantity': int(row.get('quantity', 0)) if pd.notna(row.get('quantity')) else 0,
                    'amount': float(row.get('amount', 0)) if pd.notna(row.get('amount')) else 0,
                    'sale_date': pd.to_datetime(row.get('sale_date')) if pd.notna(row.get('sale_date')) else None,
                    'row_data': row.to_dict()
                }
                
                if record['order_number'] and record['part_number']:
                    records.append(record)
            except Exception as e:
                logger.warning(f"解析第 {idx+1} 行時發生錯誤: {str(e)}")
                continue
        
        return records
    
    @staticmethod
    def parse_shelf_life_code(df: pd.DataFrame) -> List[Dict]:
        """
        解析 Shelf Life Code 統計報表
        預期欄位: 零件編號, 分類(零件/配件/精品), Shelf Life Code
        """
        records = []
        df.columns = df.columns.str.strip()
        
        column_mapping = {
            '零件編號': 'part_number',
            '零件编号': 'part_number',
            '料號': 'part_number',
            '分類': 'category',
            '分类': 'category',
            '類別': 'category',
            '类别': 'category',
            'Shelf Life Code': 'shelf_life_code',
            'ShelfLifeCode': 'shelf_life_code',
            '說明': 'description',
            '说明': 'description'
        }
        
        df = df.rename(columns=column_mapping)
        
        for idx, row in df.iterrows():
            try:
                record = {
                    'part_number': str(row.get('part_number', '')).strip(),
                    'category': str(row.get('category', '未分類')).strip(),
                    'shelf_life_code': str(row.get('shelf_life_code', '')).strip(),
                    'description': str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None
                }
                
                if record['part_number']:
                    records.append(record)
            except Exception as e:
                logger.warning(f"解析第 {idx+1} 行時發生錯誤: {str(e)}")
                continue
        
        return records
    
    @staticmethod
    def parse_technician_performance(df: pd.DataFrame, factory_code: str) -> List[Dict]:
        """
        解析技師績效報表
        預期欄位: 工單號, 技師姓名, 工時, 工資, 獎金, 日期
        """
        records = []
        df.columns = df.columns.str.strip()
        
        column_mapping = {
            '工單號': 'order_number',
            '工单号': 'order_number',
            '工單': 'order_number',
            '技師': 'technician_name',
            '技师': 'technician_name',
            '姓名': 'technician_name',
            '工時': 'work_hours',
            '工时': 'work_hours',
            '工資': 'salary',
            '工资': 'salary',
            '薪資': 'salary',
            '獎金': 'bonus',
            '奖金': 'bonus',
            '日期': 'performance_date',
            '績效日期': 'performance_date'
        }
        
        df = df.rename(columns=column_mapping)
        
        for idx, row in df.iterrows():
            try:
                record = {
                    'factory_code': factory_code,
                    'order_number': str(row.get('order_number', '')).strip() if pd.notna(row.get('order_number')) else None,
                    'technician_name': str(row.get('technician_name', '')).strip(),
                    'work_hours': float(row.get('work_hours', 0)) if pd.notna(row.get('work_hours')) else 0,
                    'salary': float(row.get('salary', 0)) if pd.notna(row.get('salary')) else 0,
                    'bonus': float(row.get('bonus', 0)) if pd.notna(row.get('bonus')) else 0,
                    'performance_date': pd.to_datetime(row.get('performance_date')) if pd.notna(row.get('performance_date')) else None,
                    'row_data': row.to_dict()
                }
                
                if record['technician_name']:
                    records.append(record)
            except Exception as e:
                logger.warning(f"解析第 {idx+1} 行時發生錯誤: {str(e)}")
                continue
        
        return records
    
    @staticmethod
    def parse_maintenance_income(df: pd.DataFrame, factory_code: str) -> List[Dict]:
        """
        解析維修收入分類報表
        預期欄位: 工單號, 收入類別, 金額, 日期
        """
        records = []
        df.columns = df.columns.str.strip()
        
        column_mapping = {
            '工單號': 'order_number',
            '工单号': 'order_number',
            '工單': 'order_number',
            '收入類別': 'income_category',
            '收入类别': 'income_category',
            '類別': 'income_category',
            '类别': 'income_category',
            '金額': 'amount',
            '金额': 'amount',
            '日期': 'income_date',
            '收入日期': 'income_date'
        }
        
        df = df.rename(columns=column_mapping)
        
        for idx, row in df.iterrows():
            try:
                record = {
                    'factory_code': factory_code,
                    'order_number': str(row.get('order_number', '')).strip(),
                    'income_category': str(row.get('income_category', '')).strip(),
                    'amount': float(row.get('amount', 0)) if pd.notna(row.get('amount')) else 0,
                    'income_date': pd.to_datetime(row.get('income_date')) if pd.notna(row.get('income_date')) else None,
                    'row_data': row.to_dict()
                }
                
                if record['order_number']:
                    records.append(record)
            except Exception as e:
                logger.warning(f"解析第 {idx+1} 行時發生錯誤: {str(e)}")
                continue
        
        return records

