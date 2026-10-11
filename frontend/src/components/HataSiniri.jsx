// [2026-10-11] React hata sınırı: bir bileşen çökerse tüm sayfa beyaza dönmesin; hata sunucuya bildirilir.
import { Component } from 'react'
import { hataBildir } from '../yardimci/hataBildir'

export default class HataSiniri extends Component {
  constructor(props) {
    super(props)
    this.state = { hata: null }
  }

  static getDerivedStateFromError(hata) {
    return { hata }
  }

  componentDidCatch(hata, bilgi) {
    hataBildir(hata, 'react', { bilesenYigini: bilgi?.componentStack })
  }

  render() {
    if (!this.state.hata) return this.props.children
    // Yeni sürüm yayımlandıktan sonra eski parça dosyası bulunamazsa: sayfayı yenilemek yeter
    const parca = /dynamically imported module|Loading chunk|Importing a module script failed/i.test(this.state.hata?.message || '')
    return (
      <div style={{ minHeight: '60vh', display: 'grid', placeItems: 'center', padding: 24 }}>
        <div className="card" style={{ maxWidth: 460, textAlign: 'center' }}>
          <div style={{ fontSize: 34, marginBottom: 6 }}>🌱</div>
          <div className="lt" style={{ marginBottom: 6 }}>
            {parca ? 'Uygulama güncellendi' : 'Bir şeyler ters gitti'}
          </div>
          <div className="ld" style={{ marginBottom: 16 }}>
            {parca
              ? 'Yeni sürümü yüklemek için sayfayı yenileyin.'
              : 'Bu ekran beklenmedik bir hatayla karşılaştı. Sorun kaydedildi; sayfayı yenileyerek devam edebilirsiniz.'}
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn" onClick={() => window.location.reload()}>Sayfayı yenile</button>
            <button className="btn sec" onClick={() => { window.location.href = '/' }}>Ana sayfaya dön</button>
          </div>
        </div>
      </div>
    )
  }
}
