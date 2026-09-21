import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [estado, setEstado] = useState<string>('conectando...')

  useEffect(() => {
    fetch('/api/zonas/', { credentials: 'same-origin' })
      .then((res) => setEstado(res.ok ? 'API disponible' : `API responde ${res.status}`))
      .catch(() => setEstado('API no disponible'))
  }, [])

  return (
    <main>
      <h1>LabCore</h1>
      <p>Sistema de gestión para laboratorio clínico</p>
      <p>Estado de la API: {estado}</p>
    </main>
  )
}

export default App