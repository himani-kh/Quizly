import sqlite3

# Connect to your existing SQLite database
conn = sqlite3.connect("quiz.db")  # change the name if needed
cursor = conn.cursor()

# Create usersAttended table
cursor.execute("""
CREATE TABLE IF NOT EXISTS usersAttended (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roomNumber TEXT,
    studentName TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    FOREIGN KEY (roomNumber) REFERENCES rooms(roomNumber)
)
""")

conn.commit()
conn.close()
print("usersAttended table created successfully!")
