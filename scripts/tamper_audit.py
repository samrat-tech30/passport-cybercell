"""Demo only: secretly flip one DENY to ALLOW in the audit log, to show the hash chain catches it.

    cd backend && .venv/bin/python ../scripts/tamper_audit.py        (Windows: .venv\\Scripts\\python ..\\scripts\\tamper_audit.py)

Then press "Verify chain" in the Audit tab -> "Chain broken at row #N". Uses DATA_DIR like the backend.
"""

import os
import sqlite3
import sys
from pathlib import Path

db = Path(os.environ.get("DATA_DIR", "var")) / "passport.db"
if not db.exists():
    sys.exit(f"No database at {db}. Run from backend/ after a demo run.")
con = sqlite3.connect(db)
row = con.execute(
    "SELECT seq FROM audit_log WHERE kind = 'decision' AND payload LIKE '%\"verdict\":\"DENY\"%' ORDER BY seq LIMIT 1"
).fetchone()
if not row:
    sys.exit("No DENY decision in the audit log yet. Run S2 with the shield on first.")
con.execute(
    "UPDATE audit_log SET payload = replace(payload, '\"verdict\":\"DENY\"', '\"verdict\":\"ALLOW\"') WHERE seq = ?", row
)
con.commit()
print(f"Tampered with audit row #{row[0]}: DENY -> ALLOW. Now press 'Verify chain'.")
