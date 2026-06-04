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

-- 開啟 Foreign Key 支援
PRAGMA foreign_keys = ON;

-- 建立使用者資料表 (積分與等級系統)
CREATE TABLE IF NOT EXISTS users (
    session_id TEXT PRIMARY KEY,
    nickname TEXT NOT NULL,
    points INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 建立設備資料表
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 建立狀態紀錄表 (擴充 reporter_session 與 is_valid)
CREATE TABLE IF NOT EXISTS status_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('available', 'queuing', 'maintenance')),
    reported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reporter_session TEXT,
    is_valid INTEGER DEFAULT 1, -- 1 = 有效, 0 = 異常已過濾
    FOREIGN KEY(equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    FOREIGN KEY(reporter_session) REFERENCES users(session_id) ON DELETE SET NULL
);

-- 建立互助驗證資料表 (防止重複驗證)
CREATE TABLE IF NOT EXISTS verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status_log_id INTEGER NOT NULL,
    verifier_session TEXT NOT NULL,
    verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(status_log_id) REFERENCES status_logs(id) ON DELETE CASCADE,
    FOREIGN KEY(verifier_session) REFERENCES users(session_id) ON DELETE CASCADE,
    UNIQUE(status_log_id, verifier_session)
);

-- 建立索引以加速查詢最新狀態
CREATE INDEX IF NOT EXISTS idx_status_logs_equipment_time ON status_logs(equipment_id, reported_at DESC);
CREATE INDEX IF NOT EXISTS idx_status_logs_valid ON status_logs(is_valid);

-- 寫入預設示範用設備資料
INSERT OR IGNORE INTO equipment (id, name, category, location) VALUES
(1, '圖書館 1F 影印機', 'printer', '圖書館一樓自習區旁'),
(2, '圖書館 3F 飲水機', 'water_dispenser', '圖書館三樓電梯口旁'),
(3, '計算機中心公用電腦', 'computer', '資訊大樓二樓 201 電腦教室'),
(4, '學生活動中心 1F 影印機', 'printer', '學生活動中心一樓超商旁'),
(5, '共同教室大樓 2F 飲水機', 'water_dispenser', '共同教室二樓走廊盡頭'),
(6, '綜合體育館 1F 飲水機', 'water_dispenser', '體育館一樓服務台對面');


