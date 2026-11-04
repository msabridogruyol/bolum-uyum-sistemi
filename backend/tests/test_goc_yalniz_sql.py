"""[2026-11-04] Canlıda OTOMATIK göçler app/core/sema_guncelleme.py ile yalnızca modülün SQL metninden uygulanır; upgrade()
çalışmaz. 0097 tohumları ilk hâlinde upgrade() içinde Python ile yazılmıştı: testler geçti (test şeması upgrade() da çalıştırır)
ama canlıda tablo bile kurulmadı. Bu test, OTOMATIK listesindeki her göçün tüm işini SQL'de yapmasını zorunlu kılar."""
import importlib.util
import inspect
import re

from app.core.sema_guncelleme import OTOMATIK, OTOMATIK_GECE, _SURUMLER


def test_otomatik_goclerin_isi_yalniz_sql_de():
    for ad in OTOMATIK + OTOMATIK_GECE:
        spec = importlib.util.spec_from_file_location(f"_g_{ad}", _SURUMLER / f"{ad}.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        assert isinstance(getattr(m, "SQL", None), str) and m.SQL.strip(), f"{ad}: SQL metni yok"
        govde = inspect.getsource(m.upgrade).split(":", 1)[1]
        for yasak in (r"\bget_bind\b", r"\btext\(", r"\b(bag|conn|baglanti)\.execute"):
            assert not re.search(yasak, govde), f"{ad}: upgrade() SQL dışında iş yapıyor ({yasak}); canlıda çalışmaz"
