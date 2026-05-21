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
