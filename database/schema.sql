CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    latitude REAL,
    longitude REAL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER NOT NULL,
    crowd_level TEXT CHECK(crowd_level IN ('low', 'medium', 'high')),
    temperature_felt TEXT CHECK(temperature_felt IN ('cold', 'comfort', 'hot')),
    user_ip TEXT,
    user_session TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(location_id) REFERENCES locations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS historical_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    crowd_level INTEGER NOT NULL, -- 0 to 100
    temperature REAL NOT NULL, -- in degrees Celsius
    FOREIGN KEY(location_id) REFERENCES locations(id) ON DELETE CASCADE
);

-- Index for querying recent reports and historical data faster
CREATE INDEX IF NOT EXISTS idx_reports_location_time ON reports(location_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_historical_location_time ON historical_data(location_id, timestamp DESC);
