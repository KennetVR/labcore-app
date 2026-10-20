import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { allPages, api } from '../api/client'
import type { Customer, Exam, ExamTariff, Package, PackageTariff, Zone } from '../api/types'

const money = (price: string) => `S/ ${Number(price).toFixed(2)}`

function TariffForm({ mode, exams, packages, zones, clients, onCancel, onSaved }: {
  mode: 'exams' | 'packages'
  exams: Exam[]
  packages: Package[]
  zones: Zone[]
  clients: Customer[]
  onCancel: () => void
  onSaved: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const text = (name: string) => String(data.get(name) ?? '').trim()
    const target = mode === 'exams' ? text('examen') : text('paquete')
    if (!target) { setError('Elegí un elemento para tarifar.'); return }
    const payload = {
      [mode === 'exams' ? 'examen' : 'paquete']: Number(target),
      precio: text('precio'),
      zona: text('zona') ? Number(text('zona')) : null,
      cliente: text('cliente') ? Number(text('cliente')) : null,
      vigencia_desde: text('vigencia_desde') || null,
      activo: data.get('activo') === 'on',
    }
    setBusy(true); setError('')
    try {
      await api(mode === 'exams' ? '/tarifario-examenes/' : '/tarifario-paquetes/', {
        method: 'POST', body: JSON.stringify(payload),
      })
      onSaved()
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar la tarifa.') }
    finally { setBusy(false) }
  }

  return <form className="panel form-panel" onSubmit={submit}>
    <h2>Datos de la tarifa</h2>
    <div className="field-grid">
      {mode === 'exams'
        ? <label>Examen<select name="examen" defaultValue="" required><option value="" disabled>Seleccioná un examen</option>{exams.map(e => <option key={e.id} value={e.id}>{e.codigo} - {e.nombre}</option>)}</select></label>
        : <label>Paquete<select name="paquete" defaultValue="" required><option value="" disabled>Seleccioná un paquete</option>{packages.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}</select></label>}
      <label>Precio<input name="precio" type="number" step="0.01" min="0" required /></label>
      <label>Zona<select name="zona" defaultValue=""><option value="">Todas las zonas</option>{zones.map(z => <option key={z.id} value={z.id}>{z.nombre}</option>)}</select></label>
      <label>Cliente<select name="cliente" defaultValue=""><option value="">Todos los clientes</option>{clients.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></label>
      <label>Vigencia desde<input name="vigencia_desde" type="date" /></label>
    </div>
    <label className="check"><input type="checkbox" name="activo" defaultChecked /> Tarifa activa</label>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="form-actions">
      <button disabled={busy}>{busy ? 'Guardando…' : 'Guardar tarifa'}</button>
      <button type="button" className="secondary" disabled={busy} onClick={onCancel}>Cancelar</button>
    </div>
  </form>
}

export default function Tariffs() {
  const [exams, setExams] = useState<Exam[]>([])
  const [packages, setPackages] = useState<Package[]>([])
  const [zones, setZones] = useState<Zone[]>([])
  const [clients, setClients] = useState<Customer[]>([])
  const [examTariffs, setExamTariffs] = useState<ExamTariff[]>([])
  const [packageTariffs, setPackageTariffs] = useState<PackageTariff[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [tab, setTab] = useState<'exams' | 'packages'>('exams')
  const [open, setOpen] = useState(false)
  const [revision, refresh] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal
    Promise.all([
      allPages<Exam>('/examenes/', signal),
      allPages<Package>('/paquetes/', signal),
      allPages<Zone>('/zonas/', signal),
      allPages<Customer>('/clientes/', signal),
      allPages<ExamTariff>('/tarifario-examenes/', signal),
      allPages<PackageTariff>('/tarifario-paquetes/', signal),
    ])
      .then(([foundExams, foundPackages, foundZones, foundClients, foundExamTariffs, foundPackageTariffs]) => {
        setExams(foundExams); setPackages(foundPackages); setZones(foundZones); setClients(foundClients)
        setExamTariffs(foundExamTariffs); setPackageTariffs(foundPackageTariffs)
      })
      .catch(e => { if (!signal.aborted) setError(e.message) })
      .finally(() => { if (!signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [revision])

  const text = query.toLocaleLowerCase()
  const visibleExams = examTariffs.filter(t => `${t.examen_codigo} ${t.examen_nombre} ${t.zona_nombre ?? ''} ${t.cliente_nombre ?? ''}`.toLocaleLowerCase().includes(text))
  const visiblePackages = packageTariffs.filter(t => `${t.paquete_nombre} ${t.zona_nombre ?? ''} ${t.cliente_nombre ?? ''}`.toLocaleLowerCase().includes(text))
  const scope = (name: string | null) => name ?? 'General'

  return <>
    <div className="page-heading"><div><p className="eyebrow">PRECIOS</p><h1>Tarifarios</h1><p>Precios por examen y paquete, con alcance por zona o cliente.</p></div>
      {!open && <button onClick={() => setOpen(true)}>Nueva tarifa</button>}</div>
    {error && <div className="error" role="alert">{error} <button className="secondary" onClick={() => { setError(''); refresh(n => n + 1) }}>Reintentar</button></div>}
    {open ? <TariffForm mode={tab} exams={exams} packages={packages} zones={zones} clients={clients}
      onCancel={() => setOpen(false)} onSaved={() => { setOpen(false); refresh(n => n + 1) }} /> : <>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === 'exams'} className={tab === 'exams' ? 'nav-active' : ''} onClick={() => setTab('exams')}>Exámenes</button>
        <button role="tab" aria-selected={tab === 'packages'} className={tab === 'packages' ? 'nav-active' : ''} onClick={() => setTab('packages')}>Paquetes</button>
      </div>
      <section className="panel">
        <div className="filters"><label>Buscar<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Examen, paquete, zona o cliente" /></label></div>
        {loading ? <p role="status" className="empty">Cargando tarifarios…</p> : tab === 'exams' ? <>
          <div className="table-scroll"><table><thead><tr><th>Examen</th><th>Precio</th><th>Zona</th><th>Cliente</th><th>Vigencia</th><th>Estado</th></tr></thead>
            <tbody>{visibleExams.map(t => <tr key={t.id}><td><strong>{t.examen_codigo} - {t.examen_nombre}</strong></td><td>{money(t.precio)}</td><td>{scope(t.zona_nombre)}</td><td>{scope(t.cliente_nombre)}</td><td>{t.vigencia_desde ?? '—'}</td><td><span className={`badge ${t.activo ? 'validada' : ''}`}>{t.activo ? 'Activa' : 'Inactiva'}</span></td></tr>)}</tbody></table></div>
          {visibleExams.length === 0 && <p className="empty">No hay tarifas de exámenes.</p>}
          <p className="table-footer">{visibleExams.length} de {examTariffs.length} tarifas</p></> : <>
          <div className="table-scroll"><table><thead><tr><th>Paquete</th><th>Precio</th><th>Zona</th><th>Cliente</th><th>Vigencia</th><th>Estado</th></tr></thead>
            <tbody>{visiblePackages.map(t => <tr key={t.id}><td><strong>{t.paquete_nombre}</strong></td><td>{money(t.precio)}</td><td>{scope(t.zona_nombre)}</td><td>{scope(t.cliente_nombre)}</td><td>{t.vigencia_desde ?? '—'}</td><td><span className={`badge ${t.activo ? 'validada' : ''}`}>{t.activo ? 'Activa' : 'Inactiva'}</span></td></tr>)}</tbody></table></div>
          {visiblePackages.length === 0 && <p className="empty">No hay tarifas de paquetes.</p>}
          <p className="table-footer">{visiblePackages.length} de {packageTariffs.length} tarifas</p></>}
      </section></>}
  </>
}
