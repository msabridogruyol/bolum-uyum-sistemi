// [2026-10-13] "Gelecekteki sana mektup": öğrenci bugünkü kendini anlatır; mektup mühürlenir, seçtiği gün e-postasına gelir.
// Mühürlü mektubun metni teslim gününe kadar gösterilmez (zaman kapsülü); silinebilir, tarihi değiştirilebilir.
// Gizlilik: metin şifreli saklanır, okul / yönetim göremez, yapay zekâya gönderilmez (backend/app/core/gelecek_mektup.py).
// Yer: Profilim → Genel bakış. Uçlar: /ogrenci/gelecek-mektup
import { useEffect, useId, useRef, useState } from 'react'
import { api } from '../api/client'

const IPUCLARI = [
  'Şu an en çok neyi merak ediyorsun?',
  'Bugün seni en çok ne heyecanlandırıyor, ne kaygılandırıyor?',
  'Hangi bölümü ya da mesleği düşünüyorsun, neden?',
  'Ne olursa olsun vazgeçmek istemediğin bir şey var mı?',
  'Gelecekteki senin neyin peşinde olmasını isterdin?',
  'Kendine bir söz ver.',
]
const tarihYaz = (t) => new Date(`${t}T12:00:00`).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })

function Zarf({ m, secenekler, onDegistir, onSil }) {
  const [tarihAcik, setTarihAcik] = useState(false)
  const [silOnay, setSilOnay] = useState(false)
  const [okuAcik, setOkuAcik] = useState(false)
  if (m.acik) {
    return (
      <div className="gm-zarf acik">
        <div className="gm-zarf-ust">
          <span className="gm-zarf-ikon" aria-hidden="true">💌</span>
          <div>
            <div className="gm-zarf-baslik">{tarihYaz(m.yazildigi)} tarihinde yazdığın mektup açıldı</div>
            <div className="gm-zarf-alt">{m.durum === 'gonderildi' ? 'E-postana da gönderildi.' : 'Burada okuyabilirsin.'}</div>
          </div>
          <button type="button" className="btn sec" onClick={() => setOkuAcik(!okuAcik)} aria-expanded={okuAcik}>{okuAcik ? 'Kapat' : 'Oku'}</button>
        </div>
        {okuAcik && <div className="gm-mektup-metin" translate="no">{m.metin}</div>}
        {okuAcik && (
          <div className="gm-zarf-dugmeler">
            {silOnay
              ? <><span className="yp-ince">Mektup kalıcı olarak silinsin mi?</span><button type="button" className="btn yp-tehlike" onClick={onSil}>Evet, sil</button><button type="button" className="btn sec" onClick={() => setSilOnay(false)}>Vazgeç</button></>
              : <button type="button" className="gm-baglanti" onClick={() => setSilOnay(true)}>Mektubu sil</button>}
          </div>
        )}
      </div>
    )
  }
  return (
    <div className="gm-zarf">
      <div className="gm-zarf-ust">
        <span className="gm-muhur" aria-hidden="true">🌱</span>
        <div>
          <div className="gm-zarf-baslik">Mühürlü mektup · {tarihYaz(m.teslim_tarihi)} tarihinde açılacak</div>
          <div className="gm-zarf-alt">{`${tarihYaz(m.yazildigi)} tarihinde yazdın.`}</div>
          {m.kisisel_eposta && <div className="gm-zarf-alt">{`Kişisel e-postana da gidecek (${m.kisisel_eposta}).`}</div>}
        </div>
      </div>
      <div className="gm-zarf-dugmeler">
        {!tarihAcik && !silOnay && (
          <>
            <button type="button" className="gm-baglanti" onClick={() => setTarihAcik(true)}>Tarihi değiştir</button>
            <button type="button" className="gm-baglanti" onClick={() => setSilOnay(true)}>Sil</button>
          </>
        )}
        {tarihAcik && (
          <TarihSecici secenekler={secenekler} ilk={m.teslim_tarihi} dugme="Kaydet"
            onSec={(t) => { onDegistir(t); setTarihAcik(false) }} onVazgec={() => setTarihAcik(false)} />
        )}
        {silOnay && (
          <>
            <span className="yp-ince">Mühürlü mektup açılmadan kalıcı olarak silinsin mi?</span>
            <button type="button" className="btn yp-tehlike" onClick={onSil}>Evet, sil</button>
            <button type="button" className="btn sec" onClick={() => setSilOnay(false)}>Vazgeç</button>
          </>
        )}
      </div>
    </div>
  )
}

function TarihSecici({ secenekler, ilk, onSec, onVazgec, dugme }) {
  const eslesen = secenekler.find((s) => s.tarih === ilk)
  const [kod, setKod] = useState(eslesen?.kod || (ilk ? 'ozel' : secenekler[0]?.kod || 'ozel'))
  const [ozel, setOzel] = useState(eslesen ? '' : ilk || '')
  const tarih = kod === 'ozel' ? ozel : secenekler.find((s) => s.kod === kod)?.tarih
  const ad = useId()
  return (
    <div className="gm-tarihler" role="radiogroup" aria-label="Mektup ne zaman açılsın?">
      {secenekler.map((s) => (
        <label key={s.kod} className={`gm-tarih${kod === s.kod ? ' secili' : ''}`}>
          <input type="radio" name={ad} checked={kod === s.kod} onChange={() => setKod(s.kod)} />
          <span className="gm-tarih-ad">{s.ad}</span>
          <span className="gm-tarih-gun">{tarihYaz(s.tarih)}</span>
        </label>
      ))}
      <label className={`gm-tarih${kod === 'ozel' ? ' secili' : ''}`}>
        <input type="radio" name={ad} checked={kod === 'ozel'} onChange={() => setKod('ozel')} />
        <span className="gm-tarih-ad">Başka bir gün</span>
        <input type="date" className="gm-tarih-girdi" value={ozel} onChange={(e) => { setOzel(e.target.value); setKod('ozel') }} aria-label="Tarih" />
      </label>
      {onSec && (
        <div className="gm-zarf-dugmeler">
          <button type="button" className="btn" disabled={!tarih} onClick={() => onSec(tarih)}>{dugme}</button>
          {onVazgec && <button type="button" className="btn sec" onClick={onVazgec}>Vazgeç</button>}
        </div>
      )}
    </div>
  )
}

export default function GelecekMektup() {
  const [v, setV] = useState(null)
  const [yaz, setYaz] = useState(false)
  const [metin, setMetin] = useState('')
  const [tarih, setTarih] = useState(null)
  const [eposta, setEposta] = useState('')
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [muhurlendi, setMuhurlendi] = useState(false)
  const alan = useRef(null)
  useEffect(() => { api.gelecekMektuplarim().then((d) => { setV(d); setTarih(d.secenekler[0]?.tarih || null) }).catch(() => setV(false)) }, [])
  if (v === false || v === null) return null
  const bekleyen = v.mektuplar.filter((m) => !m.acik).length
  const ipucuEkle = (s) => {
    const yeni = `${metin}${metin && !metin.endsWith('\n') ? '\n\n' : ''}${s}\n`
    setMetin(yeni)
    setTimeout(() => { alan.current?.focus(); alan.current?.setSelectionRange(yeni.length, yeni.length) }, 0)
  }
  const islem = (p) => { setHata(null); return p.then((d) => setV({ ...v, mektuplar: d.mektuplar })).catch((e) => setHata(e.message || 'İşlem yapılamadı.')) }
  const muhurle = () => {
    setBekle(true); setHata(null)
    api.gelecekMektupYaz({ metin, teslim_tarihi: tarih, kisisel_eposta: eposta.trim() || null })
      .then((d) => { setV({ ...v, mektuplar: d.mektuplar }); setMuhurlendi(true); setMetin(''); setEposta(''); setTimeout(() => { setYaz(false); setMuhurlendi(false) }, 2200) })
      .catch((e) => setHata(e.message || 'Mektup kaydedilemedi.'))
      .finally(() => setBekle(false))
  }
  const uzunluk = metin.trim().length
  return (
    <section className="card gm">
      <div className="gm-ust">
        <span className="gm-ikon" aria-hidden="true">✉️</span>
        <div>
          <h3 className="gm-baslik">Gelecekteki sana mektup</h3>
          <p className="gm-aciklama">Bugünkü seni, yıllar sonraki sana anlat: neyi merak ettiğini, neyin peşinde olduğunu, nelerden korktuğunu.
            Mektubun mühürlenir ve seçtiğin gün e-postana gelir. Şifreli saklanır; okulun, öğretmenlerin ve Filiz göremez.</p>
        </div>
      </div>
      {v.mektuplar.length > 0 && (
        <div className="gm-zarflar">
          {v.mektuplar.map((m) => (
            <Zarf key={m.id} m={m} secenekler={v.secenekler}
              onDegistir={(t) => islem(api.gelecekMektupTarih(m.id, t))} onSil={() => islem(api.gelecekMektupSil(m.id))} />
          ))}
        </div>
      )}
      {!yaz && bekleyen < 3 && (
        <button type="button" className="btn gm-yaz-dugme" onClick={() => setYaz(true)}>{v.mektuplar.length ? 'Yeni bir mektup yaz' : 'Mektubunu yaz'}</button>
      )}
      {yaz && (
        <div className={`gm-form${muhurlendi ? ' muhurlendi' : ''}`}>
          {muhurlendi ? (
            <div className="gm-muhur-an" role="status"><span className="gm-muhur buyuk" aria-hidden="true">🌱</span>Mektubun mühürlendi. Zamanı gelince seni bulacak.</div>
          ) : (
            <>
              <div className="gm-ipuclari">
                <span className="yp-ince">Nereden başlayacağını bilemiyorsan bir soru seç:</span>
                {IPUCLARI.map((s) => <button key={s} type="button" className="gm-ipucu" onClick={() => ipucuEkle(s)}>{s}</button>)}
              </div>
              <label htmlFor="gm-metin" className="gm-etiket">Sevgili gelecekteki ben,</label>
              <textarea id="gm-metin" ref={alan} className="gm-kagit" rows={10} maxLength={v.sinirlar.en_uzun} value={metin}
                onChange={(e) => setMetin(e.target.value)} translate="no" placeholder="Bugün…" />
              <div className="gm-sayac yp-ince">{uzunluk} / {v.sinirlar.en_uzun}{uzunluk < v.sinirlar.en_kisa ? ` · en az ${v.sinirlar.en_kisa} karakter` : ''}</div>
              <div className="gm-etiket">Ne zaman açılsın?</div>
              <TarihSeciciKontrollu secenekler={v.secenekler} onDegis={setTarih} />
              <label htmlFor="gm-eposta" className="gm-etiket">Kişisel e-postan <span className="yp-ince">(isteğe bağlı)</span></label>
              <input id="gm-eposta" type="email" className="gm-eposta" value={eposta} onChange={(e) => setEposta(e.target.value)} placeholder="ornek@eposta.com" autoComplete="email" />
              <div className="yp-ince gm-not">
                Mektup hesabındaki e-postana{v.okul_eposta ? ` (${v.okul_eposta})` : ''} gönderilir. Okul e-postan mezuniyetten sonra kapanabilir; istersen kişisel e-postanı da ekle.
                {!v.eposta_acik && ' E-posta gönderimi şu an kapalı; mektubun yine de günü gelince burada açılır.'}
              </div>
              {hata && <div className="gm-hata" role="alert">{hata}</div>}
              <div className="gm-zarf-dugmeler">
                <button type="button" className="btn" disabled={bekle || uzunluk < v.sinirlar.en_kisa || !tarih} onClick={muhurle}>Mühürle</button>
                <button type="button" className="btn sec" onClick={() => setYaz(false)}>Vazgeç</button>
              </div>
            </>
          )}
        </div>
      )}
      {hata && !yaz && <div className="gm-hata" role="alert">{hata}</div>}
    </section>
  )
}

// Form içinde: seçim değiştikçe tarihi üst bileşene bildirir
function TarihSeciciKontrollu({ secenekler, onDegis }) {
  const [kod, setKod] = useState(secenekler[0]?.kod || 'ozel')
  const [ozel, setOzel] = useState('')
  useEffect(() => { onDegis(kod === 'ozel' ? (ozel || null) : secenekler.find((s) => s.kod === kod)?.tarih || null) }, [kod, ozel]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className="gm-tarihler" role="radiogroup" aria-label="Mektup ne zaman açılsın?">
      {secenekler.map((s) => (
        <label key={s.kod} className={`gm-tarih${kod === s.kod ? ' secili' : ''}`}>
          <input type="radio" name="gm-yeni-tarih" checked={kod === s.kod} onChange={() => setKod(s.kod)} />
          <span className="gm-tarih-ad">{s.ad}</span>
          <span className="gm-tarih-gun">{tarihYaz(s.tarih)}</span>
        </label>
      ))}
      <label className={`gm-tarih${kod === 'ozel' ? ' secili' : ''}`}>
        <input type="radio" name="gm-yeni-tarih" checked={kod === 'ozel'} onChange={() => setKod('ozel')} />
        <span className="gm-tarih-ad">Başka bir gün</span>
        <input type="date" className="gm-tarih-girdi" value={ozel} onChange={(e) => { setOzel(e.target.value); setKod('ozel') }} aria-label="Tarih" />
      </label>
    </div>
  )
}
