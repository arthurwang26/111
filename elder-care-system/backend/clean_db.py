import sqlite3

def clean_database():
    conn = sqlite3.connect("c:/Users/arthu/Desktop/1111/111/elder-care-system/backend/elder_care_v2.db")
    cursor = conn.cursor()
    
    # 刪除所有的事件與指標紀錄
    cursor.execute("DELETE FROM events")
    cursor.execute("DELETE FROM abnormal_events")
    cursor.execute("DELETE FROM system_metrics")
    
    # 刪除不必要的假攝影機 (除了 camera1 等等 user 可能建立的)
    cursor.execute("DELETE FROM cameras WHERE source = 'cam5.avi'")
    
    conn.commit()
    conn.close()
    print("Database cleaned up successfully!")

if __name__ == "__main__":
    clean_database()
