"""Başlangıç verisi — katmanlar (K1-K5) ve sistem parametreleri

Revision ID: 0002_baslangic_verisi
Revises: 0001_ilk_sema
Create Date: 2026-08-12
"""
from alembic import op

revision = "0002_baslangic_verisi"
down_revision = "0001_ilk_sema"
branch_labels = None
depends_on = None

_SEED = r"""
-- BAŞLANGIÇ VERİSİ — Katmanlar (sabit 5 satır)
-- ============================================================================

INSERT INTO katmanlar (kod, ad, sira, normalizasyon_agirligi, kosullu_mu) VALUES
    ('K1', 'Değerler / Motivasyon',               1, 20.00, FALSE),
    ('K2', 'Kişilik & Çalışma Tarzı',              2, 15.00, FALSE),
    ('K3', 'İş Ortamı & Profesyonel Yetkinlik',    3, 25.00, FALSE),
    ('K4', 'Alan Eğilimi & Bilişsel Stil',         4, 40.00, FALSE);

INSERT INTO katmanlar (kod, ad, sira, normalizasyon_agirligi, kosullu_mu, tetikleyici_katman_id)
    VALUES ('K5', 'Dal Derinleşme Modülü', 5, NULL, TRUE, (SELECT id FROM katmanlar WHERE kod = 'K4'));

-- Başlangıç sistem parametreleri (E8)
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama) VALUES
    ('k5_esik_puani', '80', 'K5''in bir dalı "aday" saymak için gereken min. normalize Alan Eğilimi skoru'),
    ('k5_max_dal_sayisi', '3', 'Bir öğrenci için aynı anda açılabilecek maksimum dal sayısı'),
    ('yakinsama_esik_sigma', '0.10', '3 model arası std. sapmanın "düşük güven" sayılacağı eşik'),
    ('yeniden_degerlendirme_min_gun', '120', 'İki tam değerlendirme turu arasındaki minimum gün sayısı');
"""


def upgrade():
    for statement in _SEED.split(";"):
        s = statement.strip()
        if s and not s.startswith("--"):
            op.execute(s)


def downgrade():
    op.execute("DELETE FROM sistem_parametreleri;")
    op.execute("DELETE FROM katmanlar;")
