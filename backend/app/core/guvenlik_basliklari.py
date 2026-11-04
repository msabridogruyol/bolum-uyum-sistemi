"""[2026-11-04] Güvenlik denetimi — HTTP güvenlik başlıkları (API yanıtları).

Arayüz (Vercel) başlıkları frontend/vercel.json'dadır; bunlar API'nin kendi yanıtlarına eklenir (Vercel /api/* üzerinden
aktarır, Render adresine doğrudan gelen istekler de alır). API yalnızca JSON ve indirilen dosya döndürür; hiçbir yanıt sayfa
olarak çalıştırılmamalı ya da çerçeve içine alınmamalıdır. Uygulamanın zaten koyduğu başlık ezilmez.
"""
from __future__ import annotations

BASLIKLAR = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
    (b"cross-origin-opener-policy", b"same-origin"),
]
# CSP yalnızca JSON yanıtlarına: PDF/Excel indirmelerinde tarayıcının dosya görüntüleyicisini engellememek ve geliştirme
# ortamındaki /docs sayfasını bozmamak için.
CSP_JSON = (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'")
HSTS = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")


class GuvenlikBasliklariAraKatmani:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        https = scope.get("scheme") == "https" or any(
            a == b"x-forwarded-proto" and d.split(b",")[0].strip() == b"https" for a, d in scope.get("headers") or [])

        async def gonder(mesaj):
            if mesaj["type"] == "http.response.start":
                basliklar = list(mesaj.get("headers") or [])
                var = {a.lower() for a, _ in basliklar}
                tur = next((d for a, d in basliklar if a.lower() == b"content-type"), b"")
                ekle = BASLIKLAR + ([HSTS] if https else []) + ([CSP_JSON] if tur.startswith(b"application/json") else [])
                basliklar += [(a, d) for a, d in ekle if a not in var]
                mesaj = {**mesaj, "headers": basliklar}
            await send(mesaj)

        await self.app(scope, receive, gonder)
