"""[2026-11-15] Güvenlik denetimi: CSV dışa aktarımlarında formül enjeksiyonu."""
import csv
import io
import pathlib
import re

from app.core.excel_guvenligi import csv_hucre, guvenli_csv_yazici


def test_tehlikeli_baslangiclar_metin_kalir():
    for v in ("=HYPERLINK(\"http://x\")", "+cmd|' /C calc'!A0", "-2+3", "@SUM(A1)", "\t=1", "\r=1"):
        assert csv_hucre(v) == "'" + v
    for v in ("Ayşe Yılmaz", "", "a=b", -3.5, 12, None):
        assert csv_hucre(v) == v


def test_yazici_her_hucreyi_korur():
    t = io.StringIO()
    guvenli_csv_yazici(t, delimiter=";").writerow(["=1+1", "Ali", 5])
    assert next(csv.reader(io.StringIO(t.getvalue()), delimiter=";")) == ["'=1+1", "Ali", "5"]


def test_uygulamada_korumasiz_csv_yazici_yok():
    """Yeni bir CSV dışa aktarımı csv.writer'ı doğrudan kullanırsa bu test düşer (guvenli_csv_yazici kullanılmalı)."""
    kok = pathlib.Path(__file__).resolve().parent.parent / "app"
    ihlal = [str(p.relative_to(kok)) for p in kok.rglob("*.py")
             if p.name != "excel_guvenligi.py" and re.search(r"\bcsv\.writer\(", p.read_text(encoding="utf-8"))]
    assert ihlal == []
