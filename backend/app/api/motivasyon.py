# -*- coding: utf-8 -*-
"""
[2026-10-10] Motivasyon: YKS geri sayımı, haftalık kısa motivasyon mesajı (rozetler 2026-10-11'de kaldırıldı) (11-12. sınıf öğrencisine göre).

- YKS tarihi: Genel Takvim'de (süper admin) "sınav" türünde, başlığında YKS/TYT geçen kayıt varsa o kullanılır (resmî).
  Yoksa Haziran'ın 3. cumartesisi TAHMİNİ tarih olarak gösterilir ve öğrenciye "tahmini" diye belirtilir.
- Öğrencinin gireceği YKS yılı sınıfından hesaplanır: 12 / mezun → bu eğitim yılının YKS'si, 11 → bir sonraki, …
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core.database import get_db
from app.models import Ogrenci

router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — Motivasyon"])


def _sinif_no(sinif: str | None) -> int | None:
    s = (sinif or "").lower()
    if "mezun" in s:
        return 13
    m = re.search(r"\d+", s)
    return int(m.group()) if m else None


def _tahmini_yks(yil: int) -> date:
    """Haziran'ın 3. cumartesisi (son yıllarda YKS bu hafta sonuna denk geldi)."""
    d = date(yil, 6, 1)
    ilk_cmt = d + timedelta(days=(5 - d.weekday()) % 7)
    return ilk_cmt + timedelta(weeks=2)


def _yks_tarihi(db: Session, yil: int) -> tuple[date, bool]:
    """Genel Takvim'de o yılın YKS/TYT kaydı varsa resmî tarih, yoksa tahmini tarih."""
    try:
        r = db.execute(text(
            "SELECT baslangic FROM takvim_etkinlikleri WHERE okul_id IS NULL AND ogrenci_id IS NULL AND tur = 'sinav' "
            "AND (baslik ILIKE '%YKS%' OR baslik ILIKE '%TYT%') AND EXTRACT(YEAR FROM baslangic) = :y "
            "ORDER BY baslangic LIMIT 1"), {"y": yil}).first()
        if r:
            return r[0], True
    except Exception:
        db.rollback()
    return _tahmini_yks(yil), False


def yks_bilgisi(db: Session, sinif: str | None, bugun: date | None = None) -> dict | None:
    bugun = bugun or date.today()
    no = _sinif_no(sinif)
    if no is None or no < 9:
        return None
    # Eğitim yılı Eylül'de başlar: Eylül-Aralık → gelecek yılın YKS'si; Ocak-Ağustos → bu yılın YKS'si.
    # Yaz aylarında sınıf bilgisi henüz yükseltilmemiş olsa da (11 → 12) yıl doğru çıkar.
    egitim_yili_yks = bugun.year + 1 if bugun.month >= 9 else bugun.year
    yil = egitim_yili_yks + max(0, 12 - min(no, 12))
    tarih, resmi = _yks_tarihi(db, yil)
    if tarih < bugun:   # o yılın sınavı geçtiyse (ör. Haziran sonu) bir sonraki YKS
        yil += 1
        tarih, resmi = _yks_tarihi(db, yil)
    gun = (tarih - bugun).days
    return {"ad": f"YKS {yil}", "tarih": tarih.isoformat(), "gun": gun, "hafta": gun // 7, "resmi": resmi,
            "sinif_no": no, "son_sinif": no >= 12}


# ----------------------------------------------------------------------------- haftalık mesaj
MESAJLAR = {
    "erken": [  # 9-10. sınıf
        "Şu an sınav için değil, kendini tanımak için en güzel zaman. Merak ettiğin bir bölümü bu hafta keşfet.",
        "Bugün yaptığın küçük şeyler, iki yıl sonra verdiğin kararı kolaylaştırır.",
        "Sevdiğin dersi fark et. Hangi konuda zamanın nasıl geçtiğini anlamıyorsun? İpucu orada.",
    ],
    "temel": [  # 11. sınıf
        "11. sınıf temel yılı. TYT konularını bu yıl sağlam kurarsan 12'de sadece üstüne koyarsın.",
        "Hedef bölümünü şimdiden bilmek büyük avantaj: hangi derse ne kadar yükleneceğini biliyorsun.",
        "Haftada 1 deneme alışkanlığı, sınav günü panik yerine rutin demek.",
        "Kendini başkalarıyla değil, geçen ayki hâlinle karşılaştır.",
    ],
    "uzun": [  # 12 / mezun, 200+ gün
        "Uzun bir yol ama bugün sadece bugünün işini yap. Bir konu, bir test, bir tekrar.",
        "Düzenli 2 saat, ara ara 8 saatten daha çok net getirir.",
        "Hedef bölümünü hatırla: bu çalışmanın sonunda seni bekleyen şey o.",
        "Zorlandığın konu, en çok net kazanacağın yer.",
    ],
    "tempo": [  # 100-200 gün
        "Deneme sonuçlarına not değil, harita gibi bak: hangi konuda kaybediyorsun?",
        "Yanlış defteri tut. Aynı hatayı ikinci kez yapmamak en ucuz net.",
        "Yorulduğunda mola ver, bırakma. Uyku da çalışmanın bir parçası.",
    ],
    "deneme": [  # 30-100 gün
        "Artık her deneme bir prova. Sınav saatinde çöz, sınav gibi otur.",
        "Yeni konu açma telaşı yerine bildiklerini sağlamlaştır.",
        "Kaygı normal; vücudun önemli bir şeye hazırlandığını söylüyor. Nefes al, devam et.",
    ],
    "son": [  # < 30 gün
        "Son düzlük. Uykunu, beslenmeni ve tekrarlarını koru. Mucize değil, istikrar kazandırır.",
        "Bu hafta kendine iyi davran. Bildiklerin seninle sınava girecek.",
        "Sınav bir gün; sen bir ömürsün. Elinden gelenin en iyisini yap, gerisini bırak.",
    ],
}


def haftalik_mesaj(yks: dict | None, bugun: date | None = None) -> str:
    bugun = bugun or date.today()
    if not yks:
        grup = "erken"
    elif not yks["son_sinif"]:
        grup = "temel" if yks["sinif_no"] == 11 else "erken"
    else:
        g = yks["gun"]
        grup = "son" if g < 30 else "deneme" if g < 100 else "tempo" if g < 200 else "uzun"
    liste = MESAJLAR[grup]
    return liste[bugun.isocalendar()[1] % len(liste)]


@router.get("/motivasyon")
def motivasyon(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    yks = yks_bilgisi(db, o.sinif)
    from app.core.aktiflik import aktiflik_ozeti
    # [2026-10-11] öğrencinin kendi aktiflik serisi (ana sayfa): son 14 gün
    return {"yks": yks, "mesaj": haftalik_mesaj(yks), "aktiflik": aktiflik_ozeti(db, o.id, 14)}
