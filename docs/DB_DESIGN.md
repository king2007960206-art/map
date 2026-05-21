# 資料庫設計 (DB DESIGN)

## 1. ER 圖（實體關係圖）
```mermaid
erDiagram
    LOCATION ||--o{ REPORT : has
    LOCATION {
        int id PK
        string name "地點名稱 (如：圖書館3F)"
        float latitude "緯度"
        float longitude "經度"
    }
    REPORT {
        int id PK
        int location_id FK
        string tag "體感標籤 (超冷、悶熱等)"
        string user_session "使用者 Session (防刷用)"
        datetime created_at "建立時間"
    }
```

## 2. 資料表詳細說明

### `locations` (地點資料表)
儲存校園內的主要地點與其經緯度資訊。
- `id` (INTEGER) : Primary Key, 自動遞增。
- `name` (TEXT) : 地點名稱（如「圖書館 3 樓」、「綜合教學大樓」），必填。
- `latitude` (REAL) : 緯度，供地圖顯示與距離計算，可選。
- `longitude` (REAL) : 經度，供地圖顯示與距離計算，可選。

### `reports` (體感回報資料表)
儲存使用者的即時體感回報紀錄。
- `id` (INTEGER) : Primary Key, 自動遞增。
- `location_id` (INTEGER) : Foreign Key，對應 `locations.id`，必填。
- `tag` (TEXT) : 體感標籤（超冷、悶熱、爆滿、空曠等），必填。
- `user_session` (TEXT) : 使用者識別碼（如 Cookie/Session ID），用於防止同一使用者短時間內重複回報，必填。
- `created_at` (DATETIME) : 回報送出的時間戳記，預設為 `CURRENT_TIMESTAMP`（UTC 時間），必填。

## 3. SQL 建表語法
完整的建表 SQL 語法位於 `database/schema.sql`。

## 4. Python Model 程式碼
依據系統架構，我們使用 Python 內建的 `sqlite3` 模組來操作 SQLite 資料庫。
- **`app/models/db.py`**：處理資料庫連線與初始化建表。
- **`app/models/location.py`**：處理 `locations` 資料表的 CRUD 方法。
- **`app/models/report.py`**：處理 `reports` 資料表的 CRUD 方法與防刷驗證。
# 資料庫設計文件 (DB Design)：校園設施體感地圖

## 1. ER 圖（實體關係圖）

本專案將資料切分為「設備基本資訊」與「設備狀態紀錄」兩張表，以支援即時狀態查詢與後續的歷史統計分析。兩張表為**一對多 (1:N)** 的關係。

```mermaid
erDiagram
    EQUIPMENT {
        INTEGER id PK
        TEXT name "設備名稱 (如：活動中心影印機)"
        TEXT category "設備種類 (如：printer)"
        TEXT location "放置地點 (如：學生活動中心)"
        DATETIME created_at "建檔時間"
    }
    
    STATUS_LOGS {
        INTEGER id PK
        INTEGER equipment_id FK "關聯到 EQUIPMENT.id"
        TEXT status "狀態 (available / queuing / maintenance)"
        DATETIME reported_at "回報時間"
    }

    EQUIPMENT ||--o{ STATUS_LOGS : "has"
```

---

## 2. 資料表詳細說明

### 2.1 `equipment` (設備資料表)
存放校園內設備的靜態資訊。

| 欄位名稱 | 型別 | 屬性 | 說明 |
| -------- | ---- | ---- | ---- |
| `id` | INTEGER | PK, AUTOINCREMENT | 設備唯一識別碼 |
| `name` | TEXT | NOT NULL | 設備顯示名稱 |
| `category` | TEXT | NOT NULL | 設備種類標籤（例如 `printer`, `water_dispenser`, `computer`），用於分類篩選 |
| `location` | TEXT | | 設備放置地點（選填，方便使用者辨識） |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 設備建檔時間 |

### 2.2 `status_logs` (設備狀態紀錄表)
存放使用者回報的設備動態狀態，每一筆回報都是一條獨立紀錄。要取得某設備的「最新狀態」，只需查詢該設備在時間上最新的一筆紀錄即可。

| 欄位名稱 | 型別 | 屬性 | 說明 |
| -------- | ---- | ---- | ---- |
| `id` | INTEGER | PK, AUTOINCREMENT | 紀錄唯一識別碼 |
| `equipment_id` | INTEGER | FK, NOT NULL | 關聯到 `equipment` 表的 `id` |
| `status` | TEXT | NOT NULL | 狀態值，限定為：`available` (可用), `queuing` (排隊中), `maintenance` (維修中) |
| `reported_at`| DATETIME | DEFAULT CURRENT_TIMESTAMP | 紀錄回報當下的時間 |

> **設計決策**：
> 如 PRD 與架構文件所述，我們不需要在 `equipment` 裡新增 `current_status` 欄位。所有的狀態都來自 `status_logs`，並搭配「30 分鐘自動失效」的邏輯。若設備無紀錄或最新紀錄超過 30 分鐘，系統皆視為預設的 `available`。

---

## 3. SQL 建表語法

請參考 `database/schema.sql`。

---

## 4. Python Model 程式碼

依照輕量化與降低學習門檻的原則，我們採用 Python 內建的 `sqlite3` 模組撰寫 Data Access Object (DAO) 模式的 Model。
程式碼存放在 `app/models/` 目錄中：
- `app/models/db.py`: 負責資料庫連線與初始化設定。
- `app/models/equipment.py`: 提供設備的 CRUD 與包含最新狀態的查詢。
- `app/models/status_log.py`: 提供狀態紀錄的 CRUD。
