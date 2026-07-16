import sqlite3, os

candidates = [
    'data/pimain.db',
    os.path.join('..', 'data', 'pimain.db'),
]
db_path = None
for path in candidates:
    if os.path.exists(path):
        db_path = path
        break

if db_path is None:
    print('NO_DB_FOUND')
    raise SystemExit(2)

conn = sqlite3.connect(db_path)
rows = conn.execute("PRAGMA table_info(pi_proforma_invoice_item)").fetchall()
cols = [r[1] for r in rows]
print('DB', db_path)
print('HAS detail_desc_en:', 'detail_desc_en' in cols)
print('HAS product_acquires:', 'product_acquires' in cols)
print('HAS product_color:', 'product_color' in cols)
print('ALL', cols)
