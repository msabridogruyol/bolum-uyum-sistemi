"""Yetkinlik (değişken) görünen adları sadeleştirildi — "A / B" biçimi karşıt iki şey gibi okunuyordu.

Yalnızca görünen ad değişir; kod (D1..A9), puanlar ve hesaplama aynen kalır.

Revision ID: 0019_yetkinlik_adlari
Revises: 0018_okul_bilgileri
Create Date: 2026-10-09
"""
from alembic import op

revision = "0019_yetkinlik_adlari"
down_revision = "0018_okul_bilgileri"
branch_labels = None
depends_on = None

ADLAR = {
    "D1": "Güvence ve istikrar", "D2": "Yüksek gelir", "D3": "Statü ve prestij", "D4": "Anlam ve amaç",
    "D5": "Topluma katkı", "D6": "Özerklik ve özgürlük", "D7": "Estetik ve yaratıcılık",
    "P1": "İnsanlarla çalışma (dışadönüklük)", "P2": "Uyum ve işbirliği", "P3": "Sorumluluk ve disiplin",
    "P4": "Duygusal hassasiyet", "P5": "Yeniliğe açıklık", "P6": "Dinamik ortam tercihi",
    "P7": "Belirsizlik ve risk toleransı", "P8": "Liderlik isteği",
    "I1": "Zaman yönetimi ve önceliklendirme", "I2": "Ekip ve çatışma yönetimi", "I3": "Baskı altında karar verme",
    "I4": "Etik ve dürüstlük", "I5": "İnisiyatif alma", "I6": "Eleştiriye açıklık", "I7": "Strateji ve iş dünyası yetkinliği",
    "A1": "Sayısal ve veri eğilimi", "A2": "Sözel ve dil eğilimi", "A3": "İnsan odaklı eğilim",
    "A4": "Tasarım ve uzamsal eğilim", "A5": "Doğa ve laboratuvar eğilimi", "A6": "Fiziksel ve hareket eğilimi",
    "A7": "Yapılandırılmış çalışma stili", "A8": "Büyük resmi görme (sezgisel stil)", "A9": "Girişimcilik ve ikna eğilimi",
}

SQL = "\n".join(f"UPDATE degiskenler SET ad = '{ad}' WHERE kod = '{kod}';" for kod, ad in ADLAR.items())


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
