"""
[2026-10-04] Haftalık görevler — öğrenciyi her hafta sisteme geri getiren döngü.

Her takvim haftası (Pazartesi–Pazar, Türkiye saati) öğrenciye 3 görev atanır:
  1. Yolculuğun o anki adımı  → katman / K5 / hedef seçimi / yol haritası adımı
  2. Keşif                    → bir bölümü inceleyip örnek mesleklerine bakmak
  3. Yansıtma                 → 3 kısa soruya 2 dakikalık cevap
Görevler hafta başında bir kez oluşturulur ve hafta boyunca sabit kalır.
Seri (streak): en az 2 görevi tamamlanan ardışık haftaların sayısı.
"""
import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, BigInteger, Date, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

GOREV_TURLERI = ("katman", "k5", "hedef", "plan_adimi", "kesif", "yansitma")


class OgrenciHaftalikGorev(Base):
    __tablename__ = "ogrenci_haftalik_gorev"
    __table_args__ = (
        CheckConstraint("tur IN ('katman','k5','hedef','plan_adimi','kesif','yansitma')", name="ck_ohg_tur"),
        CheckConstraint("durum IN ('bekliyor','tamamlandi')", name="ck_ohg_durum"),
        UniqueConstraint("ogrenci_id", "hafta_baslangic", "sira", name="uq_ohg_ogrenci_hafta_sira"),
        Index("ix_ohg_ogrenci_hafta", "ogrenci_id", "hafta_baslangic"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    hafta_baslangic: Mapped[date] = mapped_column(Date, nullable=False)          # o haftanın Pazartesi'si
    sira: Mapped[int] = mapped_column(Integer, nullable=False)                    # 1, 2, 3
    tur: Mapped[str] = mapped_column(String, nullable=False)
    baslik: Mapped[str] = mapped_column(String, nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String)
    ref_kod: Mapped[str | None] = mapped_column(String)                           # katman kodu / adım kodu
    ref_bolum_id: Mapped[int | None] = mapped_column(ForeignKey("bolumler.id"))   # keşif bölümü / adımın hedef bölümü
    link: Mapped[str | None] = mapped_column(String)                              # frontend yönlendirmesi
    durum: Mapped[str] = mapped_column(String, nullable=False, default="bekliyor")
    yanit: Mapped[str | None] = mapped_column(Text)                               # yansıtma cevapları (JSON)
    tamamlanma_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
