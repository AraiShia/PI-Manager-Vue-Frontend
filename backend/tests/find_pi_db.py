import sqlite3
from pathlib import Path

pi_no = 'PISMI902607052'
roots = [Path(r'e:/AI/TraeProject/PI-Manager-System')]
for root in roots:
    for db_path in root.rglob('pimain.db'):
        try:
            conn = sqlite3.connect(db_path)
            tables = [r[0] for r in conn.execute("select name from sqlite_master where type='table'").fetchall()]
            found = []
            for table in tables:
                cols = [r[1] for r in conn.execute(f'pragma table_info({table})').fetchall()]
                if 'pi_no' in cols:
                    rows = conn.execute(f"select * from {table} where pi_no = ?", (pi_no,)).fetchall()
                    if rows:
                        found.append((table, len(rows)))
            if found:
                print(db_path)
                print(found)
            conn.close()
        except Exception:
            pass
