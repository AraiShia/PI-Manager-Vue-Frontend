import sqlite3
from pathlib import Path

db_path = Path(r'e:/AI/TraeProject/PI-Manager-System/.worktrees/pyqt-to-web-migration/backend/data/pimain.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
pi = conn.execute("select id from pi_proforma_invoice where pi_no = 'PISMI902607052'").fetchone()
print('PI id', dict(pi) if pi else None)
cols = [r[1] for r in conn.execute('pragma table_info(pi_proforma_invoice_item)').fetchall()]
wanted = [c for c in cols if c in ['id', 'customer_model', 'detail_desc', 'detail_desc_en', 'customer_code', 'product_acquires', 'product_color'] or 'name' in c]
rows = conn.execute(f'select {", ".join(wanted)} from pi_proforma_invoice_item where pi_id = ?', (pi['id'],)).fetchall()
for row in rows:
    print(dict(row))
