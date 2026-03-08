import sys, os
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'sqlite:///./elder_care_v2.db'
from app.db import SessionLocal, Resident

db = SessionLocal()
residents = db.query(Resident).all()
for r in residents:
    fe = r.face_embedding
    print(f"ID={r.id} name={r.name}")
    print(f"  face_embedding type: {type(fe)}")
    print(f"  face_embedding value: {repr(fe)[:80]}")
    print(f"  bool(face_embedding): {bool(fe)}")
    print()
db.close()
