import sqlite3
c = sqlite3.connect('elder_care_v2.db')
rows = c.execute(
    "SELECT id, name, CASE WHEN face_embedding IS NULL THEN 'NULL' WHEN face_embedding = '[]' THEN 'EMPTY_LIST' WHEN face_embedding = 'null' THEN 'NULL_STR' ELSE substr(face_embedding,1,30) END as emb_preview FROM residents"
).fetchall()
print("DB residents:")
for r in rows:
    print(f"  ID={r[0]} name={r[1]} face_embedding={r[2]}")
c.close()
