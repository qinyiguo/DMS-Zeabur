-- ==========================================
-- 廠業績管理系統 - 資料庫結構
-- ==========================================

-- 1. 廠別主檔
CREATE TABLE IF NOT EXISTS factories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,  -- AMA, AMC, AMD
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入預設廠別
INSERT INTO factories (code, name) VALUES 
    ('AMA', 'AMA廠'),
    ('AMC', 'AMC廠'),
    ('AMD', 'AMD廠')
ON CONFLICT (code) DO NOTHING;

-- 2. 工單主檔 (關聯主鍵)
CREATE TABLE IF NOT EXISTS work_orders (
    id SERIAL PRIMARY KEY,
    factory_code VARCHAR(10) NOT NULL,
    order_number VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(factory_code, order_number),
    FOREIGN KEY (factory_code) REFERENCES factories(code) ON DELETE CASCADE
);

-- 3. 零件分類主檔 (從 Shelf Life Code 統計表)
CREATE TABLE IF NOT EXISTS part_categories (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(20) NOT NULL,  -- 零件/配件/精品
    shelf_life_code VARCHAR(50),
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 零件出貨記錄
CREATE TABLE IF NOT EXISTS part_shipments (
    id SERIAL PRIMARY KEY,
    factory_code VARCHAR(10) NOT NULL,
    order_number VARCHAR(50) NOT NULL,
    part_number VARCHAR(50) NOT NULL,
    quantity INTEGER DEFAULT 0,
    amount DECIMAL(12, 2) DEFAULT 0,
    shipment_date DATE,
    file_upload_id VARCHAR(100),
    row_data JSONB,  -- 儲存原始行資料
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (factory_code, order_number) REFERENCES work_orders(factory_code, order_number) ON DELETE CASCADE,
    FOREIGN KEY (part_number) REFERENCES part_categories(part_number) ON DELETE SET NULL
);

-- 5. 零件銷售記錄
CREATE TABLE IF NOT EXISTS part_sales (
    id SERIAL PRIMARY KEY,
    factory_code VARCHAR(10) NOT NULL,
    order_number VARCHAR(50) NOT NULL,
    part_number VARCHAR(50) NOT NULL,
    quantity INTEGER DEFAULT 0,
    amount DECIMAL(12, 2) DEFAULT 0,
    sale_date DATE,
    file_upload_id VARCHAR(100),
    row_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (factory_code, order_number) REFERENCES work_orders(factory_code, order_number) ON DELETE CASCADE,
    FOREIGN KEY (part_number) REFERENCES part_categories(part_number) ON DELETE SET NULL
);

-- 6. 技師績效記錄
CREATE TABLE IF NOT EXISTS technician_performance (
    id SERIAL PRIMARY KEY,
    factory_code VARCHAR(10) NOT NULL,
    order_number VARCHAR(50),
    technician_name VARCHAR(100) NOT NULL,
    work_hours DECIMAL(8, 2) DEFAULT 0,
    salary DECIMAL(12, 2) DEFAULT 0,
    bonus DECIMAL(12, 2) DEFAULT 0,
    performance_date DATE,
    file_upload_id VARCHAR(100),
    row_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (factory_code, order_number) REFERENCES work_orders(factory_code, order_number) ON DELETE CASCADE
);

-- 7. 維修收入分類記錄
CREATE TABLE IF NOT EXISTS maintenance_income (
    id SERIAL PRIMARY KEY,
    factory_code VARCHAR(10) NOT NULL,
    order_number VARCHAR(50) NOT NULL,
    income_category VARCHAR(100),
    amount DECIMAL(12, 2) DEFAULT 0,
    income_date DATE,
    file_upload_id VARCHAR(100),
    row_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (factory_code, order_number) REFERENCES work_orders(factory_code, order_number) ON DELETE CASCADE
);

-- 8. 檔案上傳記錄 (避免重複上傳)
CREATE TABLE IF NOT EXISTS file_uploads (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    factory_code VARCHAR(10),
    file_type VARCHAR(50),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processed',
    error_message TEXT,
    uploaded_by VARCHAR(100)
);

-- ==========================================
-- 建立索引提升查詢效能
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_work_orders_factory ON work_orders(factory_code);
CREATE INDEX IF NOT EXISTS idx_work_orders_number ON work_orders(order_number);
CREATE INDEX IF NOT EXISTS idx_part_shipments_order ON part_shipments(factory_code, order_number);
CREATE INDEX IF NOT EXISTS idx_part_shipments_part ON part_shipments(part_number);
CREATE INDEX IF NOT EXISTS idx_part_sales_order ON part_sales(factory_code, order_number);
CREATE INDEX IF NOT EXISTS idx_part_sales_part ON part_sales(part_number);
CREATE INDEX IF NOT EXISTS idx_technician_factory ON technician_performance(factory_code);
CREATE INDEX IF NOT EXISTS idx_technician_name ON technician_performance(technician_name);
CREATE INDEX IF NOT EXISTS idx_maintenance_order ON maintenance_income(factory_code, order_number);
CREATE INDEX IF NOT EXISTS idx_file_hash ON file_uploads(file_hash);
CREATE INDEX IF NOT EXISTS idx_file_type ON file_uploads(file_type);

-- ==========================================
-- 建立 Views 用於業績查詢
-- ==========================================

-- 廠業績總覽
CREATE OR REPLACE VIEW v_factory_performance AS
SELECT 
    f.code as factory_code,
    f.name as factory_name,
    COUNT(DISTINCT wo.order_number) as total_orders,
    COALESCE(SUM(mi.amount), 0) as total_income,
    COALESCE(SUM(ps.amount), 0) as parts_sales,
    COALESCE(SUM(psh.amount), 0) as parts_shipments,
    COALESCE(SUM(tp.salary + tp.bonus), 0) as total_labor_cost,
    COALESCE(SUM(mi.amount), 0) - COALESCE(SUM(tp.salary + tp.bonus), 0) as net_profit
FROM factories f
LEFT JOIN work_orders wo ON f.code = wo.factory_code
LEFT JOIN maintenance_income mi ON wo.factory_code = mi.factory_code AND wo.order_number = mi.order_number
LEFT JOIN part_sales ps ON wo.factory_code = ps.factory_code AND wo.order_number = ps.order_number
LEFT JOIN part_shipments psh ON wo.factory_code = psh.factory_code AND wo.order_number = psh.order_number
LEFT JOIN technician_performance tp ON wo.factory_code = tp.factory_code AND wo.order_number = tp.order_number
GROUP BY f.code, f.name;

-- 技師績效總覽
CREATE OR REPLACE VIEW v_technician_performance_summary AS
SELECT 
    tp.technician_name,
    tp.factory_code,
    f.name as factory_name,
    COUNT(DISTINCT tp.order_number) as total_orders,
    SUM(tp.work_hours) as total_hours,
    SUM(tp.salary) as total_salary,
    SUM(tp.bonus) as total_bonus,
    SUM(tp.salary + tp.bonus) as total_income,
    CASE 
        WHEN SUM(tp.work_hours) > 0 THEN SUM(tp.salary + tp.bonus) / SUM(tp.work_hours)
        ELSE 0 
    END as avg_hourly_rate
FROM technician_performance tp
LEFT JOIN factories f ON tp.factory_code = f.code
GROUP BY tp.technician_name, tp.factory_code, f.name;

-- 零件銷售統計
CREATE OR REPLACE VIEW v_part_sales_summary AS
SELECT 
    ps.part_number,
    pc.category,
    pc.description,
    COUNT(*) as transaction_count,
    SUM(ps.quantity) as total_quantity,
    SUM(ps.amount) as total_amount,
    AVG(ps.amount) as avg_amount
FROM part_sales ps
LEFT JOIN part_categories pc ON ps.part_number = pc.part_number
GROUP BY ps.part_number, pc.category, pc.description;

-- ==========================================
-- 建立觸發器：自動更新 updated_at
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_work_orders_updated_at BEFORE UPDATE ON work_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_part_categories_updated_at BEFORE UPDATE ON part_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
