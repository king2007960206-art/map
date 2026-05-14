# 路由設計 (ROUTES)

## 1. 路由總覽表格

| 功能 | HTTP 方法 | URL 路徑 | 對應模板 | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| 首頁 (地圖與列表) | GET | `/` | `templates/index.html` | 顯示各地點最新狀態與地圖介面 |
| 獲取地點狀態列表 | GET | `/api/locations` | — (回傳 JSON) | 供前端 AJAX 非同步取得各地點最新狀態 |
| 提交體感回報 | POST | `/api/report` | — (回傳 JSON) | 接收前端的標籤與定位，存入資料庫 |
| 管理員數據看板 | GET | `/admin/dashboard` | `templates/dashboard.html` | 顯示各區歷史體感統計與圖表 |

---

## 2. 每個路由的詳細說明

### 首頁 (GET `/`)
- **輸入**：無
- **處理邏輯**：呼叫 `Location.get_all()` 取得所有地點，並透過 `Report.get_recent_by_location()` 取得各區最新的體感狀態。
- **輸出**：渲染 `index.html`，並將地點與狀態資料傳入。
- **錯誤處理**：若資料庫連線失敗，顯示 500 錯誤頁面。

### 獲取地點狀態列表 (GET `/api/locations`)
- **輸入**：無
- **處理邏輯**：取得所有地點及其最新的體感狀態、更新時間。
- **輸出**：回傳 JSON 格式資料（如 `[{"id": 1, "name": "圖書館", "tag": "超冷", "time": "2 mins ago"}]`）。
- **錯誤處理**：回傳 JSON 格式的錯誤訊息與 500 狀態碼。

### 提交體感回報 (POST `/api/report`)
- **輸入**：JSON Payload 包含 `location_id` (整數) 與 `tag` (字串)。
- **處理邏輯**：
  1. 取得使用者的 Session 或 Cookie 作為識別碼 (`user_session`)。
  2. 呼叫 `Report.check_recent_user_report(location_id, user_session)` 檢查是否在 5 分鐘內對同地點重複回報。
  3. 若驗證通過，呼叫 `Report.create(location_id, tag, user_session)` 新增紀錄。
- **輸出**：成功回傳 `{"status": "success", "message": "回報成功"}` 與 200 狀態碼。
- **錯誤處理**：
  - 若欄位缺失：回傳 400 Bad Request。
  - 若觸發防刷機制：回傳 429 Too Many Requests 與錯誤訊息。

### 管理員數據看板 (GET `/admin/dashboard`)
- **輸入**：無（未來可加入時間區間篩選參數如 `?days=7`）
- **處理邏輯**：呼叫 `Report.get_all()` 取得歷史回報資料，並計算各地點的「悶熱/超冷/爆滿/空曠」比例。
- **輸出**：渲染 `dashboard.html`，將統計數據傳入前端供圖表繪製。

---

## 3. Jinja2 模板清單

- `templates/base.html`
  - 說明：共用版型，包含 HTML `<head>`（載入 CSS、JS、地圖 API）與共用的導覽列 (Navbar)。
- `templates/index.html`
  - 說明：首頁介面，繼承自 `base.html`。包含「地圖預覽區」、「地點狀態清單」與「三秒回報按鈕」的 UI。
- `templates/dashboard.html`
  - 說明：管理員頁面，繼承自 `base.html`。包含各區塊的數據統計與圓餅圖/長條圖容器。
