from app.db import SessionLocal, Camera

db = SessionLocal()
cams = db.query(Camera).all()
for c in cams:
    c.status = 'active'
    print(f"Reset: ID:{c.id} name:{c.name} -> status:active")
db.commit()
db.close()
print("Done!")
