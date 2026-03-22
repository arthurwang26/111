import sqlite3
import os

db_path = "c:/Users/arthu/Desktop/1111/111/elder-care-system/backend/elder_care_v2.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("DELETE FROM cameras")
# Restore the original cameras
cursor.execute("INSERT INTO cameras (id, name, source, status) VALUES (2, '1', 'http://192.168.1.113:8080/video', 'offline')")
cursor.execute("INSERT INTO cameras (id, name, source, status) VALUES (3, '2', 'http://192.168.1.105:8080/video', 'offline')")
cursor.execute("INSERT INTO cameras (id, name, source, status) VALUES (4, '3', 'http://192.168.1.109:8080/video', 'offline')")
# Add cam5.avi as an explicit 4th camera so the frontend can choose it
cursor.execute("INSERT INTO cameras (id, name, source, status) VALUES (5, 'Test Video (cam5.avi)', 'cam5.avi', 'offline')")
conn.commit()
conn.close()
print("Restored IP Cameras and Added Test Video!")
