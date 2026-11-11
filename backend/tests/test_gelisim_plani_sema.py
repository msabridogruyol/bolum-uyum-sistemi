"""
[2026-11-11] Canlı hata: GET /koclugu/hedef/plan → 500 (GelisimPlaniOut ... adimlar.N.sure Field required).
Gelişim adımlarından süre kaldırılmış (f409f53), API şeması ise `sure`yi zorunlu tutuyordu. Plan uç noktasının testi
bölüm ağırlığı verisi gerektirdiği için CI'da atlanıyordu; bu test veritabanı olmadan bütün adım içeriğini şemadan geçirir.
"""
from app.core.gelisim_icerigi import ICERIK
from app.core.koclugu_servisi import _adim
from app.schemas.koclugu import PlanAdimiOut


def test_butun_gelisim_adimlari_plan_semasina_uyar():
    sayi = 0
    for kod, ic in ICERIK.items():
        for grup, anahtar in (("G", "gelisim"), ("U", "guclu")):
            for sira, ham in enumerate(ic.get(anahtar) or [], 1):
                PlanAdimiOut(**_adim(kod, kod, grup, sira, ham, "Örnek Bölüm", {}))
                sayi += 1
    assert sayi > 50
