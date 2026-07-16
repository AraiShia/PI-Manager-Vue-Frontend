import sqlite3
from pathlib import Path

pi_no = 'PISMI902607052'
db_path = Path(r'e:/AI/TraeProject/PI-Manager-System/.worktrees/pyqt-to-web-migration/backend/data/pimain.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
pi = conn.execute('select id, pi_no from pi_proforma_invoice where pi_no = ?', (pi_no,)).fetchone()
print('DB', db_path)
print('PI', dict(pi) if pi else None)
if pi:
    cols = [r[1] for r in conn.execute('pragma table_info(pi_proforma_invoice_item)').fetchall()]
    wanted = [c for c in ['id', 'pi_id', 'detail_desc', 'detail_desc_en', 'customer_model', 'customer_code'] if c in cols]
    rows = conn.execute(f"select {', '.join(wanted)} from pi_proforma_invoice_item where pi_id = ? order by id limit 10", (pi['id'],)).fetchall()
    for row in rows:
        print(dict(row))
conn.close()
