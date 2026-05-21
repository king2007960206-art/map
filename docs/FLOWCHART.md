# 系統流程圖 (FLOWCHART)

## 1. 使用者流程圖（User Flow）
此流程圖描述大學生從進入系統到完成體感回報的直覺操作路徑。

```mermaid
flowchart LR
    Start([使用者開啟網頁]) --> Home[首頁 - 體感地圖與狀態清單]
    Home --> Decision{要執行什麼操作？}
    
    Decision -->|查看各地點狀態| View[瀏覽地圖與各區體感標籤]
    View --> Home
    
    Decision -->|進行回報| Report[點擊回報按鈕]
    Report --> CheckLoc{是否允許瀏覽器獲取定位？}
    CheckLoc -->|拒絕/失敗| Manual[提供常見地點下拉選單供手動選擇]
    CheckLoc -->|允許| AutoLoc[自動帶入使用者目前所在位置]
    
    Manual --> SelectTag[點擊體感標籤 (如：超冷、悶熱、爆滿、空曠)]
    AutoLoc --> SelectTag
    
    SelectTag --> Submit[前端發送回報資料]
    Submit --> Success([顯示回報成功，更新首頁資訊])
```

## 2. 系統序列圖（Sequence Diagram）
此序列圖展示使用者送出「體感回報」時，系統前後端與資料庫的完整互動與資料流。
# 流程圖與路由對照文件 (Flowchart)：校園設施體感地圖

本文件描述了使用者的操作流程（User Flow）、系統回報狀態的詳細資料流（Sequence Diagram），以及對應的路由端點清單。

## 1. 使用者流程圖 (User Flow)

描述使用者進入網站後，可能進行的各種操作路徑，包含瀏覽、篩選以及狀態回報。

```mermaid
flowchart LR
    Start([進入網站]) --> Home[首頁 - 設備狀態列表]
    
    Home --> Action{要執行什麼操作？}
    
    %% 篩選路徑
    Action -->|選擇篩選條件| Filter[點擊設備分類\n(如：只看飲水機)]
    Filter --> Home
    
    %% 回報路徑
    Action -->|到達現場| Report[點擊特定設備的「更新狀態」]
    Report --> SelectStatus[選擇：可用 / 排隊中 / 維修中]
    SelectStatus --> Submit[送出標註]
    Submit --> UpdateUI[畫面上即時更新為最新狀態]
    UpdateUI --> Home
    
    %% 管理員路徑
    Action -->|管理員登入/訪問| Admin[進入後台統計儀表板]
    Admin --> ViewStats[查看設備故障與排隊統計圖表]
```

---

## 2. 系統序列圖 (Sequence Diagram)：狀態回報流程

描述當使用者點擊「送出標註」時，背後的資料流如何從前端傳遞到後端 Flask，最後寫入 SQLite 資料庫並完成畫面更新。我們採用 AJAX 非同步請求，讓使用者不需重新載入頁面即可看到狀態變更。

```mermaid
sequenceDiagram
    actor User as 大學生 (使用者)
    participant Browser as 瀏覽器 (前端 JS)
    participant Flask as Flask Route (Controller)
    participant Model as Database Model
    participant DB as SQLite 資料庫

    User->>Browser: 點擊「悶熱」標籤
    Browser->>Browser: 透過 Geolocation API 獲取經緯度或選擇的地點
    Browser->>Flask: POST /api/report (攜帶體感標籤、地點資訊、時間)
    
    Flask->>Flask: 檢查 Session/Cookie 確認是否頻繁回報 (Rate Limiting)
    alt 若判斷為惡意洗版
        Flask-->>Browser: 回傳 429 Too Many Requests
        Browser-->>User: 顯示「回報過於頻繁，請稍後再試」
    else 驗證通過
        Flask->>Model: 呼叫新增回報函式 (傳入地點與標籤)
        Model->>DB: INSERT INTO reports (location_id, tag, user_session, timestamp)
        DB-->>Model: 寫入成功
        Model-->>Flask: 回傳處理成功結果
        Flask-->>Browser: 回傳 200 OK (回報成功)
        Browser-->>User: 畫面提示「回報成功」並即時更新畫面上該地點的狀態
    end
```

## 3. 功能清單對照表
列出系統主要功能及其對應的 URL 路徑與 HTTP 方法。

| 功能名稱 | URL 路徑 | HTTP 方法 | 說明 |
| :--- | :--- | :--- | :--- |
| 首頁 (地圖與狀態列表) | `/` | `GET` | 透過 Jinja2 渲染主畫面與各地點最新回報狀態 |
| 送出體感回報 | `/api/report` | `POST` | 接收前端傳來的體感標籤與座標/地點，驗證後寫入資料庫 |
| 獲取最新狀態 (供前端更新) | `/api/locations` | `GET` | 供前端非同步 (AJAX/Fetch) 更新地圖標記或列表狀態 |
| 管理員數據看板 | `/admin/dashboard` | `GET` | 透過 Jinja2 渲染歷史回報數據統計分析圖表 |
    participant Browser as 瀏覽器 (JS/Fetch API)
    participant Flask as Flask 路由 (api.py)
    participant Model as Database Model
    participant DB as SQLite
    
    User->>Browser: 點擊「排隊中」按鈕
    Browser->>Flask: POST /api/equipment/1/status { status: 'queuing' }
    
    Flask->>Model: 建立新的狀態紀錄 (StatusLog)
    Model->>DB: INSERT INTO status_logs
    DB-->>Model: 新增成功
    Model-->>Flask: 回傳更新後的狀態與時間
    
    Flask-->>Browser: HTTP 200 OK (回傳 JSON: {success: true, status: 'queuing'})
    Browser->>User: 更新設備卡片UI (按鈕變色/狀態文字改變)
```

---

## 3. 功能清單與路由對照表

以下是本專案主要功能對應的 URL 路徑與 HTTP 方法，供後續實作 API 路由時參考：

| 功能名稱 | 說明 | HTTP 方法 | URL 路徑 |
| -------- | ---- | --------- | -------- |
| **首頁與設備列表** | 顯示所有設備的當前狀態 | `GET` | `/` |
| **設備分類篩選** | 透過 Query String 進行篩選（例如 `/?category=printer`） | `GET` | `/` |
| **回報設備狀態** | 透過 AJAX 提交新的狀態標註 | `POST` | `/api/equipment/<int:equipment_id>/status` |
| **後台儀表板** | 管理員查看歷史狀態統計圖表或報表 | `GET` | `/admin` |

> **開發提示**：
> - 針對 `/api/equipment/<id>/status` 的 POST 請求，前端預計會傳送包含 `status` 欄位（`available`, `queuing`, `maintenance`）的 JSON 格式資料。
> - 在 MVP 階段，後台 `/admin` 可先做成隱藏網址或簡易版不需登入即可查看的頁面，後續若有需要再補上簡單的密碼驗證。
