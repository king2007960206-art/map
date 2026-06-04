CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    latitude REAL,
    longitude REAL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    user_session TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations (id) ON DELETE CASCADE
);
-- database/schema.sql

-- 開啟 Foreign Key 支援 (SQLite 預設是關閉的，視需要在連線時開啟，但在這裡也確保關聯定義正確)
PRAGMA foreign_keys = ON;

-- 建立設備資料表
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 建立狀態紀錄表
CREATE TABLE IF NOT EXISTS status_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('available', 'queuing', 'maintenance')),
    reported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
);

-- (可選) 建立索引以加速查詢最新狀態
CREATE INDEX IF NOT EXISTS idx_status_logs_equipment_time ON status_logs(equipment_id, reported_at DESC);

-- 預設地點資料 (僅在無重複時新增)
INSERT INTO locations (name, latitude, longitude) 
SELECT '圖書館 1 樓', 25.0421, 121.5355 
WHERE NOT EXISTS (SELECT 1 FROM locations WHERE name = '圖書館 1 樓');

INSERT INTO locations (name, latitude, longitude) 
SELECT '圖書館 2 樓', 25.0422, 121.5356 
WHERE NOT EXISTS (SELECT 1 FROM locations WHERE name = '圖書館 2 樓');

INSERT INTO locations (name, latitude, longitude) 
SELECT '學生活動中心', 25.0430, 121.5350 
WHERE NOT EXISTS (SELECT 1 FROM locations WHERE name = '學生活動中心');

INSERT INTO locations (name, latitude, longitude) 
SELECT '第二教學大樓', 25.0415, 121.5360 
WHERE NOT EXISTS (SELECT 1 FROM locations WHERE name = '第二教學大樓');

-- 預設設備資料 (僅在無重複時新增)
INSERT INTO equipment (name, category, location) 
SELECT '圖書館 1 樓公用印表機', 'printer', '圖書館 1 樓' 
WHERE NOT EXISTS (SELECT 1 FROM equipment WHERE name = '圖書館 1 樓公用印表機');

INSERT INTO equipment (name, category, location) 
SELECT '學生活動中心飲水機', 'water_dispenser', '學生活動中心' 
WHERE NOT EXISTS (SELECT 1 FROM equipment WHERE name = '學生活動中心飲水機');

INSERT INTO equipment (name, category, location) 
SELECT '第二教學大樓 3 樓公用電腦', 'computer', '第二教學大樓 3 樓' 
WHERE NOT EXISTS (SELECT 1 FROM equipment WHERE name = '第二教學大樓 3 樓公用電腦');

