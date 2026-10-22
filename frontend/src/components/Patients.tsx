import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { allPages, api } from '../api/client'
import type { Customer, Patient } from '../api/types'
import { puede } from '../api/permisos'

const sexes: Record<string, string> = { M: 'Masculino', F: 'Femenino' }

function PatientForm({ customers, patient, onCancel, onSaved }: {
  customers: Customer[]
  patient?: Patient
  onCancel: () => void
  onSaved: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const text = (name: string) => String(data.get(name) ?? '').trim()
    const payload = {
      dni: text('dni') || null,
      apellidos: text('apellidos'),
      nombres: text('nombres'),
      sexo: text('sexo') || null,
      fecha_nacimiento: text('fecha_nacimiento') || null,
      cliente: text('cliente') ? Number(text('cliente')) : null,
      observaciones: text('observaciones'),
    }
    setBusy(true); setError('')
    try {
      await api(patient ? `/pacientes/${patient.id}/` : '/pacientes/', {
        method: patient ? 'PATCH' : 'POST', body: JSON.stringify(payload),
      })
      onSaved()
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar el paciente.') }
    finally { setBusy(false) }
  }

  return <form className="panel form-panel" onSubmit={submit}>
    <h2>{patient ? 'Editar paciente' : 'Datos del paciente'}</h2>
    <div className="field-grid">
      <label>Apellidos<input name="apellidos" required maxLength={100} defaultValue={patient?.apellidos ?? ''} /></label>
      <label>Nombres<input name="nombres" required maxLength={100} defaultValue={patient?.nombres ?? ''} /></label>
      <label>DNI<input name="dni" maxLength={15} defaultValue={patient?.dni ?? ''} /></label>
      <label>Sexo<select name="sexo" defaultValue={patient?.sexo ?? ''}><option value="">Sin especificar</option><option value="M">Masculino</option><option value="F">Femenino</option></select></label>
      <label>Fecha de nacimiento<input name="fecha_nacimiento" type="date" defaultValue={patient?.fecha_nacimiento ?? ''} /></label>
      <label>Cliente<select name="cliente" defaultValue={patient?.cliente ?? ''}><option value="">Particular / sin cliente</option>{customers.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></label>
    </div>
    <label>Observaciones<textarea name="observaciones" defaultValue={patient?.observaciones ?? ''} /></label>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="form-actions">
      <button disabled={busy}>{busy ? 'Guardando…' : patient ? 'Guardar cambios' : 'Guardar paciente'}</button>
      <button type="button" className="secondary" disabled={busy} onClick={onCancel}>Cancelar</button>
    </div>
  </form>
}

export default function Patients({ role }: { role: string }) {
  const [patients, setPatients] = useState<Patient[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState<Patient | 'new' | null>(null)
  const [revision, refresh] = useState(0)
  const canEdit = puede(role, 'pacientes.editar')
  const canDelete = puede(role, 'pacientes.eliminar')

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([allPages<Patient>('/pacientes/', controller.signal), allPages<Customer>('/clientes/', controller.signal)])
      .then(([found, clients]) => { setPatients(found); setCustomers(clients) })
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [revision])

  async function remove(patient: Patient) {
    if (!window.confirm(`¿Eliminar a ${patient.nombre_completo}?`)) return
    try {
      await api(`/pacientes/${patient.id}/`, { method: 'DELETE' })
      refresh(n => n + 1)
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo eliminar el paciente.') }
  }

  const visible = patients.filter(p => `${p.nombre_completo} ${p.dni ?? ''}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()))
  const customerName = (id: number | null) => customers.find(c => c.id === id)?.nombre ?? 'Particular'

  return <>
    <div className="page-heading"><div><p className="eyebrow">PADRÓN</p><h1>Pacientes</h1><p>Consulte y registre pacientes del laboratorio.</p></div>
      {canEdit && !editing && <button onClick={() => setEditing('new')}>Nuevo paciente</button>}</div>
    {error && <div className="error" role="alert">{error} <button className="secondary" onClick={() => { setError(''); refresh(n => n + 1) }}>Reintentar</button></div>}
    {canEdit && editing ? <PatientForm customers={customers} patient={editing === 'new' ? undefined : editing}
      onCancel={() => setEditing(null)} onSaved={() => { setEditing(null); refresh(n => n + 1) }} /> : <section className="panel">
      <div className="filters"><label>Buscar<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Nombre o DNI" /></label></div>
      {loading ? <p role="status" className="empty">Cargando pacientes…</p> : <>
        <div className="table-scroll"><table><thead><tr><th>Paciente</th><th>DNI</th><th>Sexo</th><th>Nacimiento</th><th>Cliente</th><th></th></tr></thead>
          <tbody>{visible.map(p => <tr key={p.id}><td><strong>{p.nombre_completo}</strong></td><td>{p.dni || '—'}</td><td>{p.sexo ? sexes[p.sexo] ?? p.sexo : '—'}</td><td>{p.fecha_nacimiento || '—'}</td><td>{customerName(p.cliente)}</td>
            <td className="row-actions">{canEdit && <button className="link" onClick={() => setEditing(p)}>Editar</button>}{canDelete && <button className="link danger" onClick={() => remove(p)}>Eliminar</button>}</td></tr>)}</tbody></table></div>
        {visible.length === 0 && <p className="empty">No hay pacientes para mostrar.</p>}
        <p className="table-footer">{visible.length} de {patients.length} pacientes</p></>}
    </section>}
  </>
}
