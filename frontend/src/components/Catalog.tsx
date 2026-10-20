import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { allPages, api } from '../api/client'
import type { Exam, Package } from '../api/types'

const areas: Record<string, string> = { sangre: 'Sangre', aguas: 'Aguas' }
const resultTypes: Record<string, string> = { numerico: 'Numérico', texto: 'Texto' }
const frequencies: Record<string, string> = { mensual: 'Mensual', bimestral: 'Bimestral', trimestral: 'Trimestral', semestral: 'Semestral' }

function ExamForm({ onCancel, onSaved }: { onCancel: () => void; onSaved: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const text = (name: string) => String(data.get(name) ?? '').trim()
    const payload = {
      codigo: text('codigo'),
      nombre: text('nombre'),
      area: text('area') || 'sangre',
      resultado_tipo: text('resultado_tipo') || 'numerico',
      unidad: text('unidad'),
      metodo: text('metodo'),
      ref_min: text('ref_min') || null,
      ref_max: text('ref_max') || null,
      ref_texto: text('ref_texto'),
      mide_pre_post: data.get('mide_pre_post') === 'on',
      activo: data.get('activo') === 'on',
    }
    setBusy(true); setError('')
    try {
      await api('/examenes/', { method: 'POST', body: JSON.stringify(payload) })
      onSaved()
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar el examen.') }
    finally { setBusy(false) }
  }

  return <form className="panel form-panel" onSubmit={submit}>
    <h2>Datos del examen</h2>
    <div className="field-grid">
      <label>Código<input name="codigo" required maxLength={30} /></label>
      <label>Nombre<input name="nombre" required maxLength={200} /></label>
      <label>Área<select name="area" defaultValue="sangre">{Object.entries(areas).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
      <label>Tipo de resultado<select name="resultado_tipo" defaultValue="numerico">{Object.entries(resultTypes).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
      <label>Unidad<input name="unidad" maxLength={30} /></label>
      <label>Método<input name="metodo" maxLength={100} /></label>
      <label>Mínimo<input name="ref_min" type="number" step="0.0001" /></label>
      <label>Máximo<input name="ref_max" type="number" step="0.0001" /></label>
      <label>Texto de referencia<input name="ref_texto" maxLength={200} /></label>
    </div>
    <div className="checks">
      <label className="check"><input type="checkbox" name="mide_pre_post" /> Mide pre y post</label>
      <label className="check"><input type="checkbox" name="activo" defaultChecked /> Examen activo</label>
    </div>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="form-actions">
      <button disabled={busy}>{busy ? 'Guardando…' : 'Guardar examen'}</button>
      <button type="button" className="secondary" disabled={busy} onClick={onCancel}>Cancelar</button>
    </div>
  </form>
}

function PackageForm({ exams, onCancel, onSaved }: { exams: Exam[]; onCancel: () => void; onSaved: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const text = (name: string) => String(data.get(name) ?? '').trim()
    const selected = data.getAll('examen').map(value => Number(value))
    if (selected.length === 0) { setError('Elegí al menos un examen para el paquete.'); return }
    const payload = {
      nombre: text('nombre'),
      frecuencia: text('frecuencia') || 'mensual',
      activo: data.get('activo') === 'on',
      examenes: selected.map((exam, index) => ({ examen: exam, orden: index })),
    }
    setBusy(true); setError('')
    try {
      await api('/paquetes/', { method: 'POST', body: JSON.stringify(payload) })
      onSaved()
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar el paquete.') }
    finally { setBusy(false) }
  }

  return <form className="panel form-panel" onSubmit={submit}>
    <h2>Datos del paquete</h2>
    <div className="field-grid">
      <label>Nombre<input name="nombre" required maxLength={100} /></label>
      <label>Frecuencia<select name="frecuencia" defaultValue="mensual">{Object.entries(frequencies).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
    </div>
    <fieldset className="member-picker">
      <legend>Exámenes del paquete</legend>
      {exams.map(e => <label key={e.id} className="check"><input type="checkbox" name="examen" value={e.id} /> {e.codigo} - {e.nombre}</label>)}
    </fieldset>
    <label className="check"><input type="checkbox" name="activo" defaultChecked /> Paquete activo</label>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="form-actions">
      <button disabled={busy}>{busy ? 'Guardando…' : 'Guardar paquete'}</button>
      <button type="button" className="secondary" disabled={busy} onClick={onCancel}>Cancelar</button>
    </div>
  </form>
}

export default function Catalog() {
  const [exams, setExams] = useState<Exam[]>([])
  const [packages, setPackages] = useState<Package[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [tab, setTab] = useState<'exams' | 'packages'>('exams')
  const [open, setOpen] = useState<null | 'exams' | 'packages'>(null)
  const [revision, refresh] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    Promise.all([allPages<Exam>('/examenes/', controller.signal), allPages<Package>('/paquetes/', controller.signal)])
      .then(([foundExams, foundPackages]) => { setExams(foundExams); setPackages(foundPackages) })
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [revision])

  const text = query.toLocaleLowerCase()
  const visibleExams = exams.filter(e => `${e.codigo} ${e.nombre}`.toLocaleLowerCase().includes(text))
  const visiblePackages = packages.filter(p => p.nombre.toLocaleLowerCase().includes(text))

  return <>
    <div className="page-heading"><div><p className="eyebrow">CATÁLOGO</p><h1>Catálogo</h1><p>Exámenes y paquetes disponibles para las órdenes.</p></div>
      {!open && <button onClick={() => setOpen(tab)}>{tab === 'exams' ? 'Nuevo examen' : 'Nuevo paquete'}</button>}</div>
    {error && <div className="error" role="alert">{error} <button className="secondary" onClick={() => { setError(''); refresh(n => n + 1) }}>Reintentar</button></div>}
    {open === 'exams' ? <ExamForm onCancel={() => setOpen(null)} onSaved={() => { setOpen(null); refresh(n => n + 1) }} />
      : open === 'packages' ? <PackageForm exams={exams} onCancel={() => setOpen(null)} onSaved={() => { setOpen(null); refresh(n => n + 1) }} />
      : <>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === 'exams'} className={tab === 'exams' ? 'nav-active' : ''} onClick={() => setTab('exams')}>Exámenes</button>
        <button role="tab" aria-selected={tab === 'packages'} className={tab === 'packages' ? 'nav-active' : ''} onClick={() => setTab('packages')}>Paquetes</button>
      </div>
      <section className="panel">
        <div className="filters"><label>Buscar<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Código o nombre" /></label></div>
        {loading ? <p role="status" className="empty">Cargando catálogo…</p> : tab === 'exams' ? <>
          <div className="table-scroll"><table><thead><tr><th>Código</th><th>Nombre</th><th>Área</th><th>Tipo</th><th>Unidad</th><th>Estado</th></tr></thead>
            <tbody>{visibleExams.map(e => <tr key={e.id}><td><strong>{e.codigo}</strong></td><td>{e.nombre}</td><td>{areas[e.area] || e.area}</td><td>{resultTypes[e.resultado_tipo] || e.resultado_tipo}</td><td>{e.unidad || '—'}</td><td><span className={`badge ${e.activo ? 'validada' : ''}`}>{e.activo ? 'Activo' : 'Inactivo'}</span></td></tr>)}</tbody></table></div>
          {visibleExams.length === 0 && <p className="empty">No hay exámenes para mostrar.</p>}
          <p className="table-footer">{visibleExams.length} de {exams.length} exámenes</p></> : <>
          <div className="table-scroll"><table><thead><tr><th>Paquete</th><th>Frecuencia</th><th>Exámenes</th><th>Estado</th></tr></thead>
            <tbody>{visiblePackages.map(p => <tr key={p.id}><td><strong>{p.nombre}</strong></td><td>{frequencies[p.frecuencia] || p.frecuencia}</td><td>{p.examenes.length} exámenes</td><td><span className={`badge ${p.activo ? 'validada' : ''}`}>{p.activo ? 'Activo' : 'Inactivo'}</span></td></tr>)}</tbody></table></div>
          {visiblePackages.length === 0 && <p className="empty">No hay paquetes para mostrar.</p>}
          <p className="table-footer">{visiblePackages.length} de {packages.length} paquetes</p></>}
      </section></>}
  </>
}
