// [2026-10-04] E-posta gönderim fonksiyonu (Vercel Serverless Function)
//
// Neden burada? Render'ın ücretsiz planı SMTP portlarını (25/465/587) engelliyor. Backend (Render),
// e-postayı HTTPS ile bu fonksiyona iletir; fonksiyon Gmail üzerinden gönderir.
//
// Vercel > Project > Settings > Environment Variables:
//   GMAIL_ADRES            → gönderen Gmail adresi (ör. dogruyol.sabri@gmail.com)
//   GMAIL_UYGULAMA_SIFRESI → Google hesabı > Güvenlik > 2 Adımlı Doğrulama > Uygulama şifreleri (16 hane)
//   EPOSTA_GIZLI_ANAHTAR   → Render'daki EPOSTA_GIZLI_ANAHTAR ile AYNI uzun rastgele metin
// Bu anahtar olmadan gelen istekler reddedilir; böylece fonksiyonu başkası spam için kullanamaz.
import nodemailer from 'nodemailer'
import crypto from 'node:crypto'

let tasiyici = null
function tasiyiciAl() {
  if (!tasiyici) {
    tasiyici = nodemailer.createTransport({
      host: 'smtp.gmail.com',
      port: 465,
      secure: true,
      connectionTimeout: 10000,
      greetingTimeout: 10000,
      socketTimeout: 20000,
      auth: { user: process.env.GMAIL_ADRES, pass: (process.env.GMAIL_UYGULAMA_SIFRESI || '').replace(/\s+/g, '') },
    })
  }
  return tasiyici
}

function anahtarDogruMu(gelen) {
  const beklenen = process.env.EPOSTA_GIZLI_ANAHTAR || ''
  if (!beklenen || typeof gelen !== 'string') return false
  const a = Buffer.from(gelen)
  const b = Buffer.from(beklenen)
  return a.length === b.length && crypto.timingSafeEqual(a, b)
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).json({ hata: 'Yalnızca POST' })
  }
  if (!anahtarDogruMu(req.headers['x-eposta-anahtar'])) {
    return res.status(401).json({ hata: 'Yetkisiz' })
  }
  if (!process.env.GMAIL_ADRES || !process.env.GMAIL_UYGULAMA_SIFRESI) {
    return res.status(500).json({ hata: 'GMAIL_ADRES / GMAIL_UYGULAMA_SIFRESI tanımlı değil' })
  }

  let govde = req.body
  if (typeof govde === 'string') {
    try { govde = JSON.parse(govde) } catch { govde = null }
  }
  const { alici, konu, html, metin } = govde || {}
  if (typeof alici !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(alici) || alici.length > 254) {
    return res.status(400).json({ hata: 'Geçersiz alıcı' })
  }
  if (typeof konu !== 'string' || !konu || konu.length > 200 || /[\r\n]/.test(konu)) {
    return res.status(400).json({ hata: 'Geçersiz konu' })
  }
  if ((html && html.length > 100000) || (metin && metin.length > 20000)) {
    return res.status(400).json({ hata: 'İçerik çok uzun' })
  }

  try {
    await tasiyiciAl().sendMail({
      from: { name: 'Filizyol', address: process.env.GMAIL_ADRES },
      to: alici,
      subject: konu,
      text: metin || '',
      html: html || undefined,
    })
    return res.status(200).json({ gonderildi: true })
  } catch (hata) {
    console.error('E-posta gönderilemedi:', hata?.code || '', hata?.message || hata)
    return res.status(502).json({ hata: 'Gönderilemedi' })
  }
}
