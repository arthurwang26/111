from app.db import SessionLocal, Camera, Resident

db = SessionLocal()
cams = db.query(Camera).all()
res = db.query(Resident).all()

print("=== Cameras ===")
for c in cams:
    print(f"ID:{c.id} name:{c.name} source:{c.source} status:{c.status}")

print("\n=== Residents ===")
for r in res:
    print(f"ID:{r.id} name:{r.name}")

db.close()
