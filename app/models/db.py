import sqlite3
import os
import datetime
import random
import math

# Get base database path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'database.db')

def get_db_connection():
    """
    Establish and return a SQLite database connection.
    Sets row_factory to sqlite3.Row for dict-like access.
    """
    if not os.path.exists(INSTANCE_DIR):
        os.makedirs(INSTANCE_DIR)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    """
    Initialize the database, run schema.sql, and seed initial data.
    """
    schema_path = os.path.join(BASE_DIR, 'database', 'schema.sql')
    if os.path.exists(schema_path):
        conn = get_db_connection()
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("Database schema initialized successfully.")
        
        # Seed initial locations and historical data
        seed_data()
    else:
        print(f"Schema file not found at: {schema_path}")

def seed_data():
    """
    Seed locations and 7 days of hourly historical data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if locations exist
    cursor.execute("SELECT COUNT(*) FROM locations")
    count = cursor.fetchone()[0]
    
    locations = [
        {"name": "圖書館", "latitude": 24.179836, "longitude": 120.648056},
        {"name": "人言大樓", "latitude": 24.179373, "longitude": 120.649129},
        {"name": "商學院", "latitude": 24.178788, "longitude": 120.648797},
        {"name": "體育館", "latitude": 24.180252, "longitude": 120.647195}
    ]
    
    if count == 0:
        for loc in locations:
            cursor.execute(
                "INSERT INTO locations (name, latitude, longitude) VALUES (?, ?, ?)",
                (loc["name"], loc["latitude"], loc["longitude"])
            )
        conn.commit()
        print("Locations seeded.")
    
    # Check if historical data exists
    cursor.execute("SELECT COUNT(*) FROM historical_data")
    hist_count = cursor.fetchone()[0]
    
    if hist_count == 0:
        print("Seeding 7 days of historical time-series data...")
        
        # Fetch the seeded locations with their ids
        cursor.execute("SELECT id, name FROM locations")
        seeded_locs = cursor.fetchall()
        
        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(days=7)
        
        # We will insert hourly data from 7 days ago to the current hour
        current_time = start_time
        records_to_insert = []
        
        while current_time <= now:
            hour = current_time.hour
            weekday = current_time.weekday() # 0 = Monday, 6 = Sunday
            is_weekend = (weekday >= 5)
            
            for loc in seeded_locs:
                loc_id = loc[0]
                name = loc[1]
                
                # Base crowd levels by hour and location type
                if name == "圖書館":
                    if hour >= 23 or hour < 7:
                        base_crowd = random.randint(2, 10)
                    elif 8 <= hour <= 12:
                        base_crowd = random.randint(45, 75)
                    elif 13 <= hour <= 17:
                        base_crowd = random.randint(70, 95)
                    elif 18 <= hour <= 22:
                        base_crowd = random.randint(55, 80)
                    else: # 7:00-8:00, 12:00-13:00
                        base_crowd = random.randint(25, 45)
                        
                elif name == "體育館":
                    if hour >= 22 or hour < 6:
                        base_crowd = random.randint(0, 5)
                    elif 6 <= hour <= 9: # Early morning workout
                        base_crowd = random.randint(20, 45)
                    elif 10 <= hour <= 15:
                        base_crowd = random.randint(30, 60)
                    elif 16 <= hour <= 21: # Prime gym hours
                        base_crowd = random.randint(75, 95)
                    else:
                        base_crowd = random.randint(15, 30)
                        
                elif name == "人言大樓" or name == "商學院":
                    # Academic buildings peak during class sessions
                    if hour >= 22 or hour < 7:
                        base_crowd = random.randint(0, 5)
                    elif 8 <= hour <= 12: # Morning classes
                        base_crowd = random.randint(65, 90)
                    elif 12 <= hour <= 13: # Lunch break slump
                        base_crowd = random.randint(20, 40)
                    elif 14 <= hour <= 17: # Afternoon classes
                        base_crowd = random.randint(70, 95)
                    elif 18 <= hour <= 21: # Evening classes
                        base_crowd = random.randint(30, 55)
                    else:
                        base_crowd = random.randint(10, 20)
                else:
                    # Default for any other location names (e.g. 圖書館 1 樓, 學生活動中心, etc.)
                    if hour >= 23 or hour < 7:
                        base_crowd = random.randint(0, 10)
                    elif 8 <= hour <= 12:
                        base_crowd = random.randint(40, 70)
                    elif 13 <= hour <= 17:
                        base_crowd = random.randint(60, 85)
                    elif 18 <= hour <= 22:
                        base_crowd = random.randint(30, 60)
                    else:
                        base_crowd = random.randint(15, 35)
                
                # Adjust for weekend
                if is_weekend:
                    if name in ["人言大樓", "商學院"]:
                        # Very few people in class buildings on weekends
                        base_crowd = int(base_crowd * 0.1)
                    else:
                        # Library/Gym have moderate weekend crowds
                        base_crowd = int(base_crowd * 0.5)
                
                # Ensure boundary
                crowd = max(0, min(100, base_crowd + random.randint(-5, 5)))
                
                # Base outdoor temperature (diurnal pattern)
                # Taichung average outdoor temp: low of 21°C around 5am, high of 31°C around 2pm
                temp_wave = math.sin((hour - 8) * math.pi / 12) # peaks at hour=14
                outdoor_temp = 25.0 + 6.0 * temp_wave + random.uniform(-1.0, 1.0)
                
                # Location adjustment
                if name == "體育館":
                    # Harder to cool, heat from people
                    loc_temp = outdoor_temp + (crowd / 100.0) * 2.0
                elif name == "圖書館":
                    # Strong AC
                    loc_temp = 22.5 + random.uniform(-0.5, 0.5)
                else: # 人言大樓, 商學院
                    # Moderate AC
                    loc_temp = 24.0 + (outdoor_temp - 24.0) * 0.2 + random.uniform(-0.5, 0.5)
                
                records_to_insert.append((
                    loc_id,
                    current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    crowd,
                    round(loc_temp, 1)
                ))
            
            current_time += datetime.timedelta(hours=1)
            
        # Batch insert to database
        cursor.executemany(
            "INSERT INTO historical_data (location_id, timestamp, crowd_level, temperature) VALUES (?, ?, ?, ?)",
            records_to_insert
        )
        conn.commit()
        print(f"Seeded {len(records_to_insert)} historical data points.")
        
    conn.close()
