# -*- coding: utf-8 -*-
"""
[2026-11-03] Filiz kriz ifadesinde okul yetkilisine bildirim.

Önce: kriz ifadesi algılandığında öğrenciye sabit kriz cevabı veriliyordu (112, ALO 183, güvendiğin bir yetişkin) ama
okuldaki hiç kimse bundan haberdar olmuyordu.
Şimdi: sistem parametresi filiz_kriz_okul_bildirimi açıksa (boş = kapalı, '*' = bütün okullar, '3,7' = bu okullar),
KESİN kriz ifadesinde (kural katmanı; yalnız sınıflandırıcının "olası" dediği mesajlarda DEĞİL) öğrencinin okulundaki okul
yetkililerine uygulama içi + e-posta bildirimi gider. Bildirimde öğrencinin adı ve sınıfı vardır, MESAJIN İÇERİĞİ YOKTUR
(veri en aza indirme). Aynı öğrenci için 24 saatte en çok bir bildirim. Okulun paketinde bildirim modülü olmasa da gider
(güvenlik bildirimi). Öğrenciye bildirildiği söylenir (KRIZ_OKUL_EKI).
Varsayılan kapalıdır: açmadan önce KVKK aydınlatma metni bu aktarımı kapsayacak biçimde güncellenmeli ve okulla bir kriz
protokolü (kim, ne kadar sürede, nasıl görüşür) yazılmalıdır.
"""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

log = logging.getLogger("kriz_bildirimi")
PARAMETRE = "filiz_kriz_okul_bildirimi"
KRIZ_OKUL_EKI = (" Okulundaki yetkili öğretmene de seninle görüşmesi için kısa bir bilgi gönderildi; ne yazdığın "
                 "paylaşılmadı.")


def acik_mi(db: Session, okul_id: int | None) -> bool:
    if not okul_id:
        return False
    from app.core.katman_servisi import parametre_oku
    deger = (parametre_oku(db, PARAMETRE, "") or "").strip()
    if not deger:
        return False
    return deger == "*" or str(okul_id) in {x.strip() for x in deger.split(",")}


def okula_bildir(db: Session, ogrenci) -> bool:
    """Okul ayarı açıksa okul yetkililerine bildirim satırlarını ekler (commit çağıranda). Döner: bildirim gitti mi."""
    okul_id = getattr(ogrenci, "okul_id", None)
    if not acik_mi(db, okul_id):
        return False
    try:
        with db.begin_nested():         # hata olursa öğrencinin kriz cevabı yine kaydedilsin
            return _ekle(db, ogrenci, okul_id)
    except Exception:
        log.exception("kriz bildirimi eklenemedi")
        return False


def _ekle(db: Session, ogrenci, okul_id: int) -> bool:
    # [2026-11-03] Okul panelinde öğrenci detayı ?sekme=ogrenciler&ogrenci=… ile açılır (yalnızca ?ogrenci= Özet sekmesinde kalıyordu)
    link = f"/admin/okul/{okul_id}?sekme=ogrenciler&ogrenci={ogrenci.id}"
    yakin = db.execute(text("""SELECT 1 FROM bildirimler WHERE tur = 'kriz_uyarisi' AND link = :l
                               AND olusturulma_zamani > now() - interval '24 hours' LIMIT 1"""), {"l": link}).first()
    if yakin:
        return True             # son 24 saatte zaten bildirildi; öğrenciye yine "bilgi gönderildi" denir
    idler = [r[0] for r in db.execute(text("""SELECT id FROM admin_kullanicilar
                                               WHERE okul_id = :o AND rol = 'okul_yetkilisi' AND aktif_mi"""),
                                      {"o": okul_id}).all()]
    if not idler:
        return False
    sinif = " / ".join(x for x in (getattr(ogrenci, "sinif", None), getattr(ogrenci, "sube", None)) if x)
    baslik = f"Öğrenciyle görüşmeniz gerekebilir: {ogrenci.ad_soyad}"
    metin = (f"{ogrenci.ad_soyad}{f' ({sinif})' if sinif else ''} Filiz'e yazdığı bir mesajda kriz ifadesi kullandı. "
             "Lütfen öğrenciyle en kısa sürede görüşün ve okulunuzun kriz protokolünü uygulayın. Mesajın içeriği "
             "gizlilik nedeniyle paylaşılmaz. Öğrenciye 112 ve ALO 183 bilgisi verildi.")
    for i in idler:
        db.execute(text("""INSERT INTO bildirimler (alici_tipi, alici_id, okul_id, tur, baslik, metin, link, eposta_durum)
                           VALUES ('yonetim', :a, :o, 'kriz_uyarisi', :b, :m, :l, 'bekliyor')"""),
                   {"a": i, "o": okul_id, "b": baslik[:200], "m": metin[:600], "l": link})
    from app.core.bildirim import kuyruk_tetikle
    kuyruk_tetikle()
    return True
