"""
İlk süper admin hesabını oluşturur — API üzerinden DEĞİL, doğrudan
veritabanına yazan bir komut satırı aracı. Bilinçli olarak API'de yok
(bkz. README "İlk admin hesabının nasıl oluşturulacağı" notu): kimin
admin olacağı herkese açık bir uç noktadan değil, sunucuya erişimi olan
biri tarafından kontrollü şekilde belirlenmeli.

Kullanım:
    python scripts/ilk_admin_olustur.py --email sen@ornek.com --ad-soyad "Adın Soyadın"

Şifre komut satırı argümanı olarak İSTENMEZ (shell geçmişinde/process
listesinde görünmesin diye) — çalıştırıldığında güvenli şekilde sorulur.
"""
import argparse
import getpass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import sifre_hashle
from app.models import AdminKullanici


def main():
    parser = argparse.ArgumentParser(description="İlk süper admin hesabını oluşturur.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--ad-soyad", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        mevcut = db.query(AdminKullanici).filter(AdminKullanici.email == args.email).first()
        if mevcut is not None:
            print(f"HATA: '{args.email}' e-postasıyla zaten bir yönetici hesabı var.")
            sys.exit(1)

        toplam_admin = db.query(AdminKullanici).count()
        if toplam_admin > 0:
            onay = input(
                f"UYARI: Veritabanında zaten {toplam_admin} admin hesabı var. "
                f"Bu script normalde yalnızca İLK admini oluşturmak içindir — "
                f"yeni yöneticileri artık /admin/yoneticiler API'sinden eklemelisiniz. "
                f"Yine de devam etmek istiyor musunuz? (evet/hayır): "
            )
            if onay.strip().lower() != "evet":
                print("İptal edildi.")
                sys.exit(0)

        sifre = getpass.getpass("Şifre (en az 8 karakter): ")
        if len(sifre) < 8:
            print("HATA: Şifre en az 8 karakter olmalı.")
            sys.exit(1)
        sifre_tekrar = getpass.getpass("Şifre (tekrar): ")
        if sifre != sifre_tekrar:
            print("HATA: Şifreler eşleşmiyor.")
            sys.exit(1)

        admin = AdminKullanici(
            ad_soyad=args.ad_soyad, email=args.email,
            sifre_hash=sifre_hashle(sifre), rol="super_admin",
        )
        db.add(admin)
        db.commit()
        print(f"✓ Süper admin hesabı oluşturuldu: {args.email}")
        print("  Artık /admin/auth/giris ile giriş yapabilir, /admin/yoneticiler ile")
        print("  ekibin geri kalanını ekleyebilirsiniz.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
