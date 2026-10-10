# -*- coding: utf-8 -*-
"""
[2026-10-10] Paketler ve modüller.

- Çekirdek (her pakette): değerlendirme, sonuçlar ve bölüm önerileri, Bölümler / Listem, profil, hedef bölüm seçimi,
  okul paneli (öğrenciler, sınıflar, okul ayarları), temel raporlar, YKS sayacı ve rozetler.
- Modüller paketlere göre açılır; okul için ayrıca tek tek eklenip çıkarılabilir:
  etkin = paketin modülleri ∪ modul_ekle − modul_cikar.
- Okul harici öğrenciler (okul_id yok) tüm modülleri görür.
- Koruma: öğrenci uçlarında ogrenci_modulu(), okul yönetimi uçlarında okul_modulu() bağımlılığı 403 döner.
"""
from __future__ import annotations

import json

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

MODULLER = {
    "bildirimler": {"ad": "Bildirimler", "ikon": "🔔", "aciklama": "Uygulama içi bildirimler ve önemli olaylarda e-posta (kulüp kararı, rehberlik randevusu, kulüp etkinliği)"},
    "kocluk": {"ad": "Koçluk ve görevler", "ikon": "🎯", "aciklama": "Koçluğum (yol haritası, Sen ve Bölümün, ilham kaynakları, tekrar ölçüm) ve haftalık Görevlerim"},
    "takvim": {"ad": "Takvim", "ikon": "🗓️", "aciklama": "Öğrenci takvimi ve okul etkinlikleri"},
    "kutuphane": {"ad": "Kütüphanem", "ikon": "📚", "aciklama": "Okuduğu kitaplar, izledikleri ve grafikler"},
    "kulupler": {"ad": "Kulüpler", "ikon": "🎭", "aciklama": "İlgi testi, kulüp önerileri, katılma talepleri ve kulüp duyuruları"},
    "filiz": {"ad": "Filiz asistanı", "ikon": "💬", "aciklama": "Filiz sohbet asistanı (otomatik rehber / yapay zekâ)"},
    "calisma": {"ad": "Çalışma programı ve soru takibi", "ikon": "⏱️", "aciklama": "Haftalık ders programı, günlük çalışma süresi ve çözülen soru kaydı, ders bazında isabet"},
    "net_takibi": {"ad": "Net takibi", "ikon": "📈", "aciklama": "Deneme netleri, konu takibi, hedef üniversiteye göre net kıyası"},
    "okul_denemeleri": {"ad": "Okul denemesi yükleme", "ikon": "🏫", "aciklama": "Okulun yaptığı denemelerin sonuçlarını Excel şablonuyla tek seferde yükleme, şube ve okul ortalamaları (Net takibi ile çalışır)"},
    "akran": {"ad": "Şube ve akran analizi", "ikon": "🤝", "aciklama": "Benzer akranlar, şube dağılımı önerisi, aday öğrenci uyumu"},
    "egitim_koclari": {"ad": "Eğitim koçları", "ikon": "👩‍🏫", "aciklama": "Anlaşmalı eğitim koçlarıyla görüşme talebi"},
    "rehberlik": {"ad": "Rehberlik ve erken uyarı", "ikon": "🧭", "aciklama": "Görüşme kayıtları, randevular, takipler ve dikkat gerektiren öğrenciler listesi"},
    "ogrenci_raporlari": {"ad": "Öğrenci raporları", "ikon": "📄", "aciklama": "Öğrenci kendi raporunu ve velisine göstereceği veli raporunu hesabından indirir (Raporlarım)"},
    "gelismis_raporlar": {"ad": "Gelişmiş raporlar", "ikon": "🗂️", "aciklama": "Şube toplu raporları ve sınıf öğretmeni raporu"},
}
TUMU = list(MODULLER)
# [2026-10-10] modül → çalışması için gereken modül
BAGIMLILIK = {"okul_denemeleri": "net_takibi"}


def _liste(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except Exception:
            return []
    return [x for x in v if x in MODULLER]


def paket_listesi(db: Session) -> list[dict]:
    rows = db.execute(text("SELECT kod, ad, aciklama, moduller, sira FROM paketler ORDER BY sira, kod")).mappings().all()
    return [{**dict(r), "moduller": _liste(r["moduller"])} for r in rows]


def okul_modulleri(db: Session, okul_id: int | None) -> list[str]:
    if not okul_id:
        return TUMU[:]
    try:
        r = db.execute(text("""
            SELECT o.paket, o.modul_ekle, o.modul_cikar, p.moduller
              FROM okullar o LEFT JOIN paketler p ON p.kod = o.paket WHERE o.id = :o"""), {"o": okul_id}).first()
    except Exception:
        db.rollback()
        return TUMU[:]   # şema henüz güncellenmediyse hiçbir şey kapanmasın
    if r is None:
        return TUMU[:]
    etkin = (set(_liste(r.moduller)) if r.paket else set(TUMU)) | set(_liste(r.modul_ekle))
    etkin -= set(_liste(r.modul_cikar))
    etkin -= {m for m, gerek in BAGIMLILIK.items() if gerek not in etkin}   # bağlı olduğu modül kapalıysa çalışamaz
    return [m for m in TUMU if m in etkin]


def okul_paket_bilgisi(db: Session, okul_id: int | None) -> dict:
    if not okul_id:
        return {"paket": None, "paket_ad": "Tümü", "moduller": TUMU[:], "paket_modulleri": TUMU[:], "ekle": [], "cikar": []}
    r = db.execute(text("SELECT o.paket, o.modul_ekle, o.modul_cikar, p.ad, p.moduller AS pm FROM okullar o LEFT JOIN paketler p ON p.kod = o.paket "
                        "WHERE o.id = :o"), {"o": okul_id}).first()
    return {"paket": r.paket if r else None, "paket_ad": (r.ad if r else None) or "—", "moduller": okul_modulleri(db, okul_id),
            "paket_modulleri": _liste(r.pm) if r else [],
            "ekle": _liste(r.modul_ekle) if r else [], "cikar": _liste(r.modul_cikar) if r else []}


def _yasak(kod: str):
    raise HTTPException(status_code=403, detail=f"“{MODULLER[kod]['ad']}” okulunuzun paketinde yer almıyor.")


def ogrenci_modulu(kod: str):
    """Öğrenci uçları için: öğrencinin okulunda modül kapalıysa 403."""
    from app.api.deps import get_mevcut_ogrenci

    def kontrol(db: Session = Depends(get_db), o=Depends(get_mevcut_ogrenci)):
        if kod not in okul_modulleri(db, o.okul_id):
            _yasak(kod)
    return kontrol


def okul_modulu(kod: str):
    """Okul yönetimi uçları için: yoldaki okul_id / ogrenci_id / kulup_id'den okul bulunur; modül kapalıysa 403.
    Süper admin her zaman geçer (önizleme ve destek için)."""
    from app.api.deps import get_mevcut_yonetim

    def kontrol(request: Request, db: Session = Depends(get_db), yon=Depends(get_mevcut_yonetim)):
        if getattr(yon, "rol", None) == "super_admin":
            return
        p = request.path_params
        okul_id = None
        try:
            if "okul_id" in p:
                okul_id = int(p["okul_id"])
            elif "ogrenci_id" in p:
                okul_id = db.execute(text("SELECT okul_id FROM ogrenciler WHERE id = CAST(:i AS UUID)"), {"i": p["ogrenci_id"]}).scalar()
            elif "kulup_id" in p:
                okul_id = db.execute(text("SELECT okul_id FROM okul_kulupleri WHERE id = :i"), {"i": int(p["kulup_id"])}).scalar()
            elif "uyelik_id" in p:
                okul_id = db.execute(text("SELECT k.okul_id FROM kulup_uyelikleri u JOIN okul_kulupleri k ON k.id = u.kulup_id "
                                          "WHERE u.id = :i"), {"i": int(p["uyelik_id"])}).scalar()
            elif "gorusme_id" in p:
                okul_id = db.execute(text("SELECT o.okul_id FROM rehberlik_gorusmeleri g JOIN ogrenciler o ON o.id = g.ogrenci_id "
                                          "WHERE g.id = :i"), {"i": int(p["gorusme_id"])}).scalar()
            elif "deneme_id" in p:
                okul_id = db.execute(text("SELECT okul_id FROM okul_denemeleri WHERE id = :i"), {"i": int(p["deneme_id"])}).scalar()
            elif "duyuru_id" in p:
                okul_id = db.execute(text("SELECT k.okul_id FROM kulup_duyurulari d JOIN okul_kulupleri k ON k.id = d.kulup_id "
                                          "WHERE d.id = :i"), {"i": int(p["duyuru_id"])}).scalar()
            else:
                okul_id = getattr(yon, "okul_id", None)
        except (ValueError, TypeError):
            db.rollback()
            return
        if okul_id and kod not in okul_modulleri(db, okul_id):
            _yasak(kod)
    return kontrol
