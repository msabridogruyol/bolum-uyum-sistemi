"""[2026-10-11] Kökteki eski test betiklerini (modül düzeyinde çalışan, kendi SQLite veritabanını kuran) AYRI süreçte
çalıştırır: DATABASE_URL'i süreç başında SQLite'a çevirdikleri için aynı pytest sürecinde içe aktarılırlarsa diğer testlerin
veritabanı motorunu bozarlar. Betikler göreli yollar (app/data/..., ./_test_*.db) kullandığı için backend/ klasöründe
çalışırlar; oluşturdukları _test_*.db dosyaları test sonunda silinir."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[1]
BETIKLER = ["test_skor_motoru.py", "test_ters_yonlu.py", "test_psikometri.py", "test_ats.py"]

# Betikler ORM şemasını SQLite'ta kurar; sabitlenmiş SQLAlchemy 2.0 PostgreSQL'e özgü JSONB'yi SQLite'ta derleyemez
# (2.1 derleyebiliyor). Betiklere dokunmadan, çalıştırmadan önce JSONB → JSON derleme kuralı eklenir.
_ON_EK = (
    "from sqlalchemy.ext.compiler import compiles\n"
    "from sqlalchemy.dialects.postgresql import JSONB\n"
    "compiles(JSONB, 'sqlite')(lambda t, c, **k: 'JSON')\n"
    "import runpy, sys\n"
    "sys.argv = [sys.argv[1]]\n"
    "runpy.run_path(sys.argv[0], run_name='__main__')\n"
)


@pytest.mark.parametrize("betik", BETIKLER)
def test_eski_betik(betik):
    onceki = set(KOK.glob("_test_*.db"))
    ortam = {**os.environ, "PYTHONPATH": str(KOK) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    ortam.pop("DATABASE_URL", None)   # betikler kendi SQLite'ını kurar; bazıları ortamdaki değeri kullanıyor olabilir
    try:
        s = subprocess.run([sys.executable, "-c", _ON_EK, str(KOK / betik)], cwd=KOK, env=ortam, capture_output=True, text=True, timeout=300)
    finally:
        for f in set(KOK.glob("_test_*.db")) - onceki:
            f.unlink(missing_ok=True)
    assert s.returncode == 0, f"{betik} başarısız:\n{s.stdout[-3000:]}\n{s.stderr[-3000:]}"
