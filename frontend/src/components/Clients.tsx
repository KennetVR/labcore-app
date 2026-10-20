import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { allPages, api } from '../api/client'
import type { Customer, Zone } from '../api/types'

const types: Record<string, string> = { clinica: 'Clínica / Consultorio', dialisis: 'Centro de diálisis' }

function ClientForm({ zones, onCancel, onSaved }: { zones: Zone[]; onCancel: () => void; onSaved: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const text = (name: string) => String(data.get(name) ?? '').trim()
    const payload = {
      nombre: text('nombre'),
      tipo: text('tipo') || 'clinica',
      zona: text('zona') ? Number(text('zona')) : null,
      contacto: text('contacto'),
      activo: data.get('activo') === 'on',
    }
    setBusy(true); setError('')
    try {
      await api('/clientes/', { method: 'POST', body: JSON.stringify(payload) })
      onSaved()
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar el cliente.') }
    finally { setBusy(false) }
  }

  return <form className="panel form-panel" onSubmit={submit}>
    <h2>Datos del cliente</h2>
    <div className="field-grid">
      <label>Nombre<input name="nombre" required maxLength={200} /></label>
      <label>Tipo<select name="tipo" defaultValue="clinica">{Object.entries(types).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
      <label>Zona<select name="zona" defaultValue=""><option value="">Sin zona</option>{zones.map(z => <option key={z.id} value={z.id}>{z.nombre}</option>)}</select></label>
      <label>Contacto<input name="contacto" maxLength={200} /></label>
    </div>
    <label className="check"><input type="checkbox" name="activo" defaultChecked /> Cliente activo</label>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="form-actions">
      <button disabled={busy}>{busy ? 'Guardando…' : 'Guardar cliente'}</button>
      <button type="button" className="secondary" disabled={busy} onClick={onCancel}>Cancelar</button>
    </div>
  </form>
}

export default function Clients() {
  const [clients, setClients] = useState<Customer[]>([])
  const [zones, setZones] = useState<Zone[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [revision, refresh] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    Promise.all([allPages<Customer>('/clientes/', controller.signal), allPages<Zone>('/zonas/', controller.signal)])
      .then(([found, zonesFound]) => { setClients(found); setZones(zonesFound) })
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [revision])

  const visible = clients.filter(c => `${c.nombre} ${c.contacto}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()))
  const zoneName = (id: number | null) => zones.find(z => z.id === id)?.nombre ?? 'Sin zona'

  return <>
    <div className="page-heading"><div><p className="eyebrow">CARTERA</p><h1>Clientes</h1><p>Clínicas, consultorios y centros de diálisis.</p></div>
      {!open && <button onClick={() => setOpen(true)}>Nuevo cliente</button>}</div>
    {error && <div className="error" role="alert">{error} <button className="secondary" onClick={() => { setError(''); refresh(n => n + 1) }}>Reintentar</button></div>}
    {open ? <ClientForm zones={zones} onCancel={() => setOpen(false)} onSaved={() => { setOpen(false); refresh(n => n + 1) }} /> : <section className="panel">
      <div className="filters"><label>Buscar<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Nombre o contacto" /></label></div>
      {loading ? <p role="status" className="empty">Cargando clientes…</p> : <>
        <div className="table-scroll"><table><thead><tr><th>Cliente</th><th>Tipo</th><th>Zona</th><th>Contacto</th><th>Estado</th></tr></thead>
          <tbody>{visible.map(c => <tr key={c.id}><td><strong>{c.nombre}</strong></td><td>{types[c.tipo] || c.tipo}</td><td>{zoneName(c.zona)}</td><td>{c.contacto || '—'}</td><td><span className={`badge ${c.activo ? 'validada' : ''}`}>{c.activo ? 'Activo' : 'Inactivo'}</span></td></tr>)}</tbody></table></div>
        {visible.length === 0 && <p className="empty">No hay clientes para mostrar.</p>}
        <p className="table-footer">{visible.length} de {clients.length} clientes</p></>}
    </section>}
  </>
}
