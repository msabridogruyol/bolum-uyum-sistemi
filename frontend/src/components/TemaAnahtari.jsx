import { useState, useEffect } from 'react'

function temaAl() {
  return localStorage.getItem('tema') || 'light'
}

export default function TemaAnahtari({ sabit = true }) {
  const [tema, setTema] = useState(temaAl())

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', tema)
    localStorage.setItem('tema', tema)
  }, [tema])

  return (
    <button
      className={sabit ? 'tema-anahtari' : 'tema-anahtari-gomulu'}
      type="button"
      onClick={() => setTema((t) => (t === 'light' ? 'dark' : 'light'))}
      title={tema === 'light' ? 'Koyu moda geç' : 'Açık moda geç'}
    >
      {tema === 'light' ? '🌙' : '☀️'}
    </button>
  )
}
