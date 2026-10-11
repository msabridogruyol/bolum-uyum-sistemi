// [2026-10-11] React hata sınırı: bir bileşen çökerse tüm sayfa beyaza dönmesin; hata sunucuya bildirilir.
import { Component } from 'react'
import { hataBildir } from '../yardimci/hataBildir'
import { surumHatasiMi, yeniSurumIcinYenile } from '../yardimci/tembelYukle'

export default class HataSiniri extends Component {
  constructor(props) {
    super(props)
    this.state = { hata: null }
  }

  static getDerivedStateFromError(hata) {
    return { hata }
  }

  componentDidCatch(hata, bilgi) {
    // [2026-10-11] Eski sürüm parçası: önce kendiliğinden bir kez yenile (hata kaydı oluşturma); olmazsa aşağıdaki ekran
    if (surumHatasiMi(hata) && yeniSurumIcinYenile()) return
    hataBildir(hata, 'react', { bilesenYigini: bilgi?.componentStack })
  }

  render() {
    if (!this.state.hata) return this.props.children
    // Yeni sürüm yayımlandıktan sonra eski parça dosyası bulunamazsa: sayfayı yenilemek yeter
    const parca = surumHatasiMi(this.state.hata)
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
