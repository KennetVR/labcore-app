import { useEffect, useState } from 'react'
import { allPages, api } from '../api/client'
import type { Customer, Exam, Item, Package, Patient, Quote } from '../api/types'
import { money } from '../api/types'

type Line = Item & { label: string }
type Catalog = { patients: Patient[]; customers: Customer[]; exams: Exam[]; packages: Package[] }
export default function OrderForm({ onCancel, onSaved }: { onCancel: () => void; onSaved: () => void }) {
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [patient, setPatient] = useState('')
  const [customer, setCustomer] = useState('')
  const [selection, setSelection] = useState('')
  const [lines, setLines] = useState<Line[]>([])
  const [note, setNote] = useState('')
  const [quote, setQuote] = useState<Quote | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    Promise.all([
      allPages<Patient>('/pacientes/', controller.signal), allPages<Customer>('/clientes/', controller.signal),
      allPages<Exam>('/examenes/', controller.signal), allPages<Package>('/paquetes/', controller.signal),
    ]).then(([patients, customers, exams, packages]) => setCatalog({ patients, customers, exams, packages }))
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
    return () => controller.abort()
  }, [retry])
  function invalidate() { setQuote(null); setError('') }
  function add() {
    if (!catalog || !selection) return
    const [kind, rawId] = selection.split(':')
    const id = Number(rawId)
    const pack = kind === 'p' ? catalog.packages.find(p => p.id === id) : undefined
    const exam = catalog.exams.find(e => e.id === (pack ? [...pack.examenes].sort((a, b) => a.orden - b.orden)[0]?.examen : id))
    if (!exam) { setError('El paquete no tiene un examen de referencia disponible.'); return }
    invalidate()
    setLines([...lines, { examen: exam.id, ...(pack ? { paquete: pack.id } : {}), cantidad: 1, medicion: 'unica', label: pack ? pack.nombre : `${exam.codigo} — ${exam.nombre}` }])
    setSelection('')
  }
  const payload = { paciente: Number(patient), cliente: customer ? Number(customer) : null,
    estado: 'registrada', observacion: note,
    items: lines.map(({ examen, paquete, cantidad, medicion }) => ({ examen, ...(paquete ? { paquete } : {}), cantidad, medicion })) }
  async function submit(save: boolean) {
    setBusy(true); setError('')
    try {
      if (save) {
        await api('/ordenes/', { method: 'POST', body: JSON.stringify(payload) })
        onSaved()
      } else setQuote(await api<Quote>('/ordenes/cotizar/', { method: 'POST', body: JSON.stringify(payload) }))
    } catch (e) { setQuote(null); setError(e instanceof Error ? e.message : 'No se pudo completar la solicitud.') }
    finally { setBusy(false) }
  }
  const valid = patient && lines.length > 0 && lines.every(l => Number.isInteger(l.cantidad) && l.cantidad > 0)
  return <>
    <div className="page-heading"><div><p className="eyebrow">NUEVA SOLICITUD</p><h1>Nueva orden</h1><p>Seleccione el paciente, agregue los estudios y consulte el precio.</p></div><button className="secondary" disabled={busy} onClick={onCancel}>Volver al listado</button></div>
    {error && <div className="error" role="alert">{error}{!catalog && <button className="secondary" onClick={() => { setError(''); setRetry(n => n + 1) }}>Reintentar</button>}</div>}
    {!catalog ? <p role="status">Cargando pacientes y catálogo…</p> : <div className="form-layout"><section className="panel form-panel"><fieldset disabled={busy}>
      <h2>1. Paciente y cliente</h2><div className="field-grid"><label>Paciente<select value={patient} onChange={e => { invalidate(); setPatient(e.target.value); setCustomer(String(catalog.patients.find(p => p.id === Number(e.target.value))?.cliente ?? '')) }}><option value="">Seleccione un paciente</option>{catalog.patients.map(p => <option key={p.id} value={p.id}>{p.nombre_completo}</option>)}</select></label>
      <label>Cliente<select value={customer} onChange={e => { invalidate(); setCustomer(e.target.value) }}><option value="">Particular / sin cliente</option>{catalog.customers.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></label></div>
      <h2>2. Exámenes y paquetes</h2><div className="add-line"><label>Examen o paquete<select value={selection} onChange={e => setSelection(e.target.value)}><option value="">Seleccioná un estudio</option><optgroup label="Paquetes">{catalog.packages.filter(p => p.activo).map(p => <option key={p.id} value={`p:${p.id}`}>{p.nombre}</option>)}</optgroup><optgroup label="Exámenes">{catalog.exams.filter(e => e.activo).map(e => <option key={e.id} value={`e:${e.id}`}>{e.codigo} — {e.nombre}</option>)}</optgroup></select></label><button type="button" disabled={!selection} onClick={add}>Agregar</button></div>
      {lines.length === 0 && <p className="empty">Agregue al menos un examen o paquete.</p>}
      {lines.map((line, i) => <div className="order-line" key={i}><div><strong>{line.label}</strong><small>{line.paquete ? 'Paquete completo · un solo cargo' : 'Examen individual'}</small></div><label>Cantidad<input aria-label={`Cantidad ${i + 1}`} type="number" min="1" step="1" value={line.cantidad} onChange={e => { invalidate(); setLines(lines.map((l, n) => n === i ? { ...l, cantidad: Number(e.target.value) } : l)) }} /></label><button className="secondary" aria-label={`Quitar ${line.label}`} onClick={() => { invalidate(); setLines(lines.filter((_, n) => n !== i)) }}>Quitar</button></div>)}
      <label>Observación<textarea value={note} onChange={e => { invalidate(); setNote(e.target.value) }} /></label>
    </fieldset></section><aside className="panel quote-panel"><p className="eyebrow">RESUMEN</p><h2>Cotización</h2>
      <p>Los precios se calculan con las tarifas vigentes del laboratorio.</p>
      {quote ? <>{quote.items.map((item, i) => <div className="quote-line" key={i}><span>{lines[i]?.label}<small>{money(item.precio_unitario)} por unidad</small></span><strong>{money(item.subtotal)}</strong></div>)}<div className="quote-total"><span>Total</span><strong>{money(quote.total)}</strong></div></> : <p className="empty">Consulte la cotización antes de guardar.</p>}
      <button className="secondary" disabled={busy || !valid} onClick={() => submit(false)}>{busy ? 'Procesando…' : 'Cotizar'}</button>
      <button disabled={busy || !valid || !quote} onClick={() => submit(true)}>Guardar orden</button>
      <small>El precio se vuelve a validar al guardar. La cotización no reserva tarifas.</small>
    </aside></div>}
  </>
}
