// [2026-10-09] Okul tanıtım kartı: öğrenci okul rozetine tıklayınca açılan pencerenin içeriği
// (yönetimdeki "Okul Bilgileri" sekmesinde canlı önizleme olarak da kullanılır).
const GOREV_SIRASI = ['Okul Müdürü', 'Müdür Başyardımcısı', 'Müdür Yardımcısı', 'Rehber Öğretmen / Psikolojik Danışman', 'Psikolog', 'Kariyer Danışmanı']

function webMetni(u) {
  return (u || '').replace(/^https?:\/\//, '').replace(/\/$/, '')
}

export default function OkulBilgiKarti({ okul }) {
  if (!okul) return null
  const kadro = [...(okul.kadro || [])].filter((k) => k.ad)
    .sort((a, b) => {
      const ia = GOREV_SIRASI.indexOf(a.gorev), ib = GOREV_SIRASI.indexOf(b.gorev)
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)
    })
  const yas = okul.kurulus_yili ? new Date().getFullYear() - okul.kurulus_yili : null
  const iletisim = okul.adres || okul.telefon || okul.eposta || okul.web
  const bos = !okul.kurulus_yili && !okul.ogrenci_sayisi && !okul.tanitim && !kadro.length && !iletisim

  return (
    <div className="okb">
      <div className="okb-ust">
        {okul.logo ? <img src={okul.logo} alt="" className="okb-logo" /> : <div className="okb-logo okb-logo-bos">🏫</div>}
        <div style={{ minWidth: 0 }}>
          <div className="okb-ad">{okul.ad}</div>
          {okul.alt_baslik && <div className="okb-alt">{okul.alt_baslik}</div>}
        </div>
      </div>

      {(okul.kurulus_yili || okul.ogrenci_sayisi) ? (
        <div className="okb-rakamlar">
          {okul.kurulus_yili && <div><b>{okul.kurulus_yili}</b><span>kuruluş yılı{yas > 0 ? ` · ${yas} yıllık` : ''}</span></div>}
          {okul.ogrenci_sayisi ? <div><b>{okul.ogrenci_sayisi.toLocaleString('tr-TR')}</b><span>öğrenci</span></div> : null}
          {kadro.length > 0 && <div><b>{kadro.length}</b><span>yönetici ve danışman</span></div>}
        </div>
      ) : null}

      {okul.tanitim && <p className="okb-tanitim">{okul.tanitim}</p>}

      {kadro.length > 0 && (
        <>
          <div className="okb-baslik">Okul kadrosu</div>
          <div className="okb-kadro">
            {kadro.map((k, i) => (
              <div key={i} className="okb-kisi">
                <div className="okb-avatar">{k.ad.trim().split(/\s+/).map((p) => p[0]).slice(0, 2).join('').toLocaleUpperCase('tr')}</div>
                <div style={{ minWidth: 0 }}>
                  <div className="okb-kisi-ad">{k.ad}</div>
                  <div className="okb-kisi-gorev">{k.gorev}</div>
                  {k.eposta && <a className="okb-link" href={`mailto:${k.eposta}`}>✉ {k.eposta}</a>}
                  {k.telefon && <a className="okb-link" href={`tel:${k.telefon.replace(/\s/g, '')}`}>☎ {k.telefon}</a>}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {iletisim && (
        <>
          <div className="okb-baslik">İletişim</div>
          <div className="okb-iletisim">
            {okul.adres && <div>📍 {okul.adres}</div>}
            {okul.telefon && <a className="okb-link" href={`tel:${okul.telefon.replace(/\s/g, '')}`}>☎ {okul.telefon}</a>}
            {okul.eposta && <a className="okb-link" href={`mailto:${okul.eposta}`}>✉ {okul.eposta}</a>}
            {okul.web && <a className="okb-link" href={okul.web} target="_blank" rel="noopener noreferrer">🌐 {webMetni(okul.web)}</a>}
          </div>
        </>
      )}

      {bos && <div className="okb-bos">Okulun tanıtım bilgileri burada görünecek.</div>}
    </div>
  )
}
