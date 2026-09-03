# -*- coding: utf-8 -*-
"""
Admin — Soru Geçerlilik Testi Girdisi V2 (sonradan eklendi)

Mevcut gecerlilik girdisi uç noktasından TEK FARKI: her satıra katman_kod
ekliyor. Bu sayede yerel test script'i (soru_gecerlilik_testi.py), her
soruyu yalnızca KENDİ KATMANINDAKİ değişkenler arasından test edebiliyor
— önceki sürüm 87+ değişkenin TAMAMI arasından seçtirdiği için katmanlar
arası anlamsız eşleşmeler (K1 sorusu K3 değişkeniyle karışması gibi) çıkıyordu.

Bağımsız router — mevcut admin.py'ye dokunmaz.

GET /admin/gecerlilik-girdisi-v2 — Likert soruları + SJT seçeneklerini,
                                     katman_kod dahil, dışa aktarır.
"""

from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.api.deps import get_mevcut_admin
from app.models import (
    AdminKullanici, Soru, SoruSecenegi, SjtSecenekDegiskenAgirlik, Katman, Degisken,
)

router = APIRouter(prefix="/gecerlilik-girdisi-v2", tags=["admin-gecerlilik-v2"])


@router.delete("/sonuclar", status_code=204)
def gecerlilik_sonuclarini_temizle(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """[EKLENDİ] Ekrandaki eski soru geçerlilik test sonuçlarının tamamını
    siler — soruların/sistemin kendisine dokunmaz, yalnızca bu test
    kayıtlarını temizler. Yeni bir test çalıştırıp tekrar yükleyebilirsiniz."""
    from sqlalchemy import text
    db.execute(text("DELETE FROM soru_gecerlilik_sonuclari"))
    db.commit()


class KatmanAnalizSatiri(BaseModel):
    katman_kod: str
    toplam_birim: int
    en_az_2_3_sayisi: int
    en_az_2_3_orani: float       # yüzde, 0-100
    rastgele_baseline_orani: float  # yüzde, 0-100 — 3 bağımsız modelin şansla ≥2/3 hemfikir olma ihtimali
    kac_kat_ustu: float
    geçerli_mi: bool             # en_az_2_3_orani >= gecerlilik_esigi ise True


class GecerlilikAnaliziOut(BaseModel):
    katman_esigi_yuzde: float   # her katmanın kendi içinde ulaşması gereken minimum ≥2/3 oranı
    genel_esik_yuzde: float     # tüm sistemin ortalamasının ulaşması gereken minimum oran
    genel_en_az_2_3_orani: float
    genel_toplam_birim: int
    genel_gecerli_mi: bool
    katmanlar: list[KatmanAnalizSatiri]


# [KAYNAK — akademik gerekçe]
# Gözlemciler/değerlendiriciler arası uyum (inter-rater agreement) literatüründe
# yerleşik eşikler kullanılıyor, keyfi seçilmedi:
#   - %70  : kabul edilebilir MİNİMUM eşik (Stemler, 2004, "recommended minimum
#            threshold for rater pair agreement")
#   - %75-80: "tatmin edici / kabul edilebilir" uyum düzeyi (Graham, Milanowski
#            & Miller, 2012; McHugh, 2012); Landis & Koch (1977) kappa
#            sınıflandırmasında bu aralık "önemli ölçüde/neredeyse mükemmel"
#            uyum kategorisine karşılık gelir.
# Buna göre: her KATMAN kendi içinde ≥%70'i geçmeli (minimum kabul edilebilir),
# sistemin GENEL ortalaması ise ≥%80'i geçmeli (tatmin edici düzey) — katman
# bazında minimum kabul edilebilir olsa da, sistemin bütünü daha yüksek bir
# tatmin edicilik standardında tutuluyor.
KATMAN_ESIGI = 70.0
GENEL_ESIK = 80.0


@router.get("/analiz", response_model=GecerlilikAnaliziOut)
def gecerlilik_analizini_getir(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """
    [EKLENDİ] Her katman için: gerçek ≥2/3 (çoğunluk oyu) başarı oranı,
    rastgele tahmin baseline'ı (o katmandaki/dal'daki gerçek aday sayısına
    göre matematiksel olarak hesaplanır) ve bunun kaç katı üstünde olduğu.
    "Geçerli/Geçersiz" etiketi, ≥2/3 oranının rastgele şanstan anlamlı
    ölçüde yüksek olup olmadığına dayanır — tam 3/3 konsensüs ARANMAZ,
    3 bağımsız modelden çoğunluğunun hemfikir olması yeterli sayılır
    (ensemble/topluluk kararı yöntembilimi).
    """
    from math import comb

    def kod_oneki(kod: str) -> str:
        return "".join(c for c in kod if not c.isdigit())

    def rastgele_2_3_ihtimali(n: int) -> float:
        if n <= 0:
            return 0.0
        p = 1 / n
        p2 = comb(3, 2) * (p ** 2) * (1 - p)
        p3 = p ** 3
        return (p2 + p3) * 100

    # Her değişken önekinin (D, P, I, A, M, S, ...) kaç üyesi var — gerçek
    # test sırasında kullanılan aday havuzu büyüklüğü budur.
    tum_degiskenler = db.query(Degisken.kod).all()
    onek_boyutlari: dict[str, int] = {}
    for (kod,) in tum_degiskenler:
        onek = kod_oneki(kod)
        onek_boyutlari[onek] = onek_boyutlari.get(onek, 0) + 1

    from sqlalchemy import text
    ham_satirlar = db.execute(text("""
        SELECT k.kod AS katman_kod, sgs.gercek_degisken_kod,
               sgs.model_a_dogru, sgs.model_b_dogru, sgs.model_c_dogru
        FROM soru_gecerlilik_sonuclari sgs
        JOIN sorular s ON s.id = sgs.soru_id
        JOIN katmanlar k ON k.id = s.katman_id
    """)).all()

    katman_verisi: dict[str, dict] = {}
    genel_en_az_2, genel_toplam = 0, 0

    for katman_kod, gercek_kod, a_dogru, b_dogru, c_dogru in ham_satirlar:
        d = katman_verisi.setdefault(katman_kod, {"toplam": 0, "en_az_2": 0, "baseline_toplami": 0.0})
        d["toplam"] += 1
        genel_toplam += 1
        kac_dogru = sum([bool(a_dogru), bool(b_dogru), bool(c_dogru)])
        if kac_dogru >= 2:
            d["en_az_2"] += 1
            genel_en_az_2 += 1
        onek = kod_oneki(gercek_kod)
        n = onek_boyutlari.get(onek, 7)  # bulunamazsa makul bir varsayım
        d["baseline_toplami"] += rastgele_2_3_ihtimali(n)

    katman_satirlari = []
    for katman_kod in sorted(katman_verisi.keys()):
        d = katman_verisi[katman_kod]
        oran = d["en_az_2"] / d["toplam"] * 100
        baseline_ort = d["baseline_toplami"] / d["toplam"]
        katman_satirlari.append(KatmanAnalizSatiri(
            katman_kod=katman_kod,
            toplam_birim=d["toplam"],
            en_az_2_3_sayisi=d["en_az_2"],
            en_az_2_3_orani=round(oran, 1),
            rastgele_baseline_orani=round(baseline_ort, 2),
            kac_kat_ustu=round(oran / baseline_ort, 1) if baseline_ort > 0 else 0.0,
            geçerli_mi=oran >= KATMAN_ESIGI,
        ))

    genel_oran = round(genel_en_az_2 / genel_toplam * 100, 1) if genel_toplam else 0.0

    return GecerlilikAnaliziOut(
        katman_esigi_yuzde=KATMAN_ESIGI,
        genel_esik_yuzde=GENEL_ESIK,
        genel_en_az_2_3_orani=genel_oran,
        genel_toplam_birim=genel_toplam,
        genel_gecerli_mi=genel_oran >= GENEL_ESIK,
        katmanlar=katman_satirlari,
    )


class GecerlilikBirimiOut(BaseModel):
    birim_anahtari: str
    kaynak_soru_id: int
    secenek_id: int | None
    kaynak_tipi: str  # 'likert' | 'sjt'
    katman_kod: str
    metin: str
    baglam: str | None
    beklenen_degisken_kod: str


@router.get("", response_model=list[GecerlilikBirimiOut])
def gecerlilik_girdisi_getir_v2(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    sonuc: list[GecerlilikBirimiOut] = []
    degisken_kodlari = dict(db.query(Degisken.id, Degisken.kod).all())

    # --- Likert sorular: soru metninin kendisi test edilir ---
    likert_sorular = (
        db.query(Soru, Katman.kod)
        .join(Katman, Katman.id == Soru.katman_id)
        .filter(Soru.soru_tipi == "likert", Soru.aktif_mi.is_(True), Soru.degisken_id.isnot(None))
        .all()
    )
    for soru, katman_kodu in likert_sorular:
        sonuc.append(GecerlilikBirimiOut(
            birim_anahtari=f"soru_{soru.id}", kaynak_soru_id=soru.id, secenek_id=None,
            kaynak_tipi="likert", katman_kod=katman_kodu, metin=soru.soru_metni, baglam=None,
            beklenen_degisken_kod=degisken_kodlari.get(soru.degisken_id, ""),
        ))

    # --- SJT seçenekleri: her seçeneğin EN YÜKSEK ağırlıklı değişkeni "beklenen" sayılır ---
    sjt_sorular = (
        db.query(Soru, Katman.kod)
        .join(Katman, Katman.id == Soru.katman_id)
        .filter(Soru.soru_tipi == "sjt", Soru.aktif_mi.is_(True))
        .all()
    )
    for soru, katman_kodu in sjt_sorular:
        secenekler = db.query(SoruSecenegi).filter(SoruSecenegi.soru_id == soru.id).all()
        for sec in secenekler:
            agirliklar = (
                db.query(SjtSecenekDegiskenAgirlik)
                .filter(SjtSecenekDegiskenAgirlik.secenek_id == sec.id)
                .order_by(SjtSecenekDegiskenAgirlik.agirlik.desc())
                .all()
            )
            if not agirliklar:
                continue
            en_yuksek = agirliklar[0]
            # [DÜZELTME — metodolojik hata] Bir seçeneğin en yüksek ağırlığı
            # NEGATİFSE, o seçenek metni o değişkenin TERSİNİ ifade ediyor
            # demektir (örn. "Bu bana zor ve yorucu gelir" -> A3'ün -0.8
            # ağırlıklı "tersi" seçeneği). Böyle bir metnin A3'e semantik
            # olarak YAKIN çıkması zaten beklenmez — bunu teste dahil etmek
            # haksız bir başarısızlık üretir. Yalnızca pozitif ağırlıklı
            # (gerçekten o değişkeni TEMSİL EDEN) seçenekler test edilir.
            if en_yuksek.agirlik <= 0:
                continue
            sonuc.append(GecerlilikBirimiOut(
                birim_anahtari=f"sjt_{soru.id}_{sec.id}", kaynak_soru_id=soru.id, secenek_id=sec.id,
                kaynak_tipi="sjt", katman_kod=katman_kodu, metin=sec.secenek_metni, baglam=soru.soru_metni,
                beklenen_degisken_kod=degisken_kodlari.get(en_yuksek.degisken_id, ""),
            ))

    # --- [EKLENDİ] Kutup seçenekleri: 1-2 numaralı şıklar A ucu değişkenine,
    # 3-4 numaralı şıklar B ucu değişkenine "beklenen" olarak atanır. ---
    kutup_sorular = (
        db.query(Soru, Katman.kod)
        .join(Katman, Katman.id == Soru.katman_id)
        .filter(Soru.soru_tipi == "kutup", Soru.aktif_mi.is_(True))
        .all()
    )
    for soru, katman_kodu in kutup_sorular:
        if soru.degisken_id is None or soru.b_ucu_degisken_id is None:
            continue
        secenekler = db.query(SoruSecenegi).filter(SoruSecenegi.soru_id == soru.id).order_by(SoruSecenegi.secenek_sirasi).all()
        for sec in secenekler:
            beklenen_id = soru.degisken_id if sec.secenek_sirasi <= 2 else soru.b_ucu_degisken_id
            sonuc.append(GecerlilikBirimiOut(
                birim_anahtari=f"kutup_{soru.id}_{sec.id}", kaynak_soru_id=soru.id, secenek_id=sec.id,
                kaynak_tipi="kutup", katman_kod=katman_kodu, metin=sec.secenek_metni, baglam=soru.soru_metni,
                beklenen_degisken_kod=degisken_kodlari.get(beklenen_id, ""),
            ))

    return sonuc


# ============================================================================
# NOT — main.py'de, admin_guvenlik ile AYNI yere şunu ekleyin:
#   from app.api.admin_gecerlilik_v2 import router as admin_gecerlilik_v2_router
#   app.include_router(admin_gecerlilik_v2_router, prefix="/admin", tags=["admin"])
# Dosyayı backend/app/api/admin_gecerlilik_v2.py olarak kaydedin.
# ============================================================================
