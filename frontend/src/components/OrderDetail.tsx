import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { OrderDetail as Order, OrderItem, EnvioReporte } from '../api/types'
import { money, orderStates, paymentMethods, paymentRoles } from '../api/types'

const measurements: Record<string, string> = { unica: 'Única', pre_post: 'Pre y post' }
const closedStates = ['validada', 'pdf', 'entregada']
const rangeLabels: Record<string, string> = { alto: 'Alto', bajo: 'Bajo', normal: 'En rango' }

type Draft = { resultado: string; bandera: string; banderaManual: boolean }

function formatRef(value: string | null): string {
  if (value === null || value === '') return ''
  const parsed = Number(value)
  return Number.isFinite(parsed) ? String(parsed) : value
}

function referenceText(item: OrderItem): string {
  const min = formatRef(item.ref_min)
  const max = formatRef(item.ref_max)
  if (min && max) return `${min} - ${max}${item.unidad ? ` ${item.unidad}` : ''}`
  if (min) return `≥ ${min}${item.unidad ? ` ${item.unidad}` : ''}`
  if (max) return `≤ ${max}${item.unidad ? ` ${item.unidad}` : ''}`
  return item.ref_texto || ''
}

export default function OrderDetail({ id, role, onBack }: { id: number; role: string; onBack: () => void }) {
  const [order, setOrder] = useState<Order | null>(null)
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [email, setEmail] = useState('')
  const [resendEmail, setResendEmail] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const [retry, setRetry] = useState(0)
  const [history, setHistory] = useState<EnvioReporte[]>([])
  const [payAmount, setPayAmount] = useState('')
  const [payMethod, setPayMethod] = useState('contado')
  const [payNote, setPayNote] = useState('')

  function load(data: Order) {
    setOrder(data)
    setDrafts(Object.fromEntries(data.items.map(item => [item.id, {
      resultado: item.resultado,
      bandera: item.bandera,
      banderaManual: item.bandera_manual,
    }])))
  }

  useEffect(() => {
    const controller = new AbortController()
    api<Order>(`/ordenes/${id}/`, { signal: controller.signal })
      .then(load)
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
    return () => controller.abort()
  }, [id, retry])

  useEffect(() => {
    if (!order) return
    let cancelled = false
    api<{ results: EnvioReporte[] }>(`/ordenes/${order.id}/envios/`)
      .then(data => { if (!cancelled) setHistory(data.results) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [order, retry])

  const editable = order !== null && !closedStates.includes(order.estado)
  const canValidate = role === 'admin' || role === 'encargada'
  const canReport = role === 'admin' || role === 'encargada' || role === 'reportes'
  const canPay = paymentRoles.includes(role)
  const complete = order !== null && order.items.length > 0
    && order.items.every(item => (drafts[item.id]?.resultado ?? '').trim() !== '')

  async function send(action: 'resultados' | 'validar', body?: unknown) {
    if (!order) return
    setBusy(action); setError('')
    try {
      load(await api<Order>(`/ordenes/${order.id}/${action}/`, { method: 'POST', body: JSON.stringify(body ?? {}) }))
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo actualizar la orden.') }
    finally { setBusy('') }
  }

  function saveResults() {
    if (!order) return
    send('resultados', {
      items: order.items.map(item => ({
        id: item.id,
        resultado: drafts[item.id]?.resultado ?? '',
        bandera: drafts[item.id]?.bandera ?? '',
        bandera_manual: Boolean(drafts[item.id]?.banderaManual ?? item.bandera_manual),
      })),
    })
  }

  async function generateReport() {
    if (!order) return
    setBusy('reporte'); setError('')
    try {
      await api(`/ordenes/${order.id}/reporte/`, { method: 'POST', body: JSON.stringify({}) })
      setRetry(n => n + 1)
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo generar el reporte.') }
    finally { setBusy('') }
  }

  async function registerDelivery() {
    if (!order) return
    setBusy('entrega'); setError('')
    try {
      load(await api<Order>(`/ordenes/${order.id}/entrega/`, {
        method: 'POST', body: JSON.stringify({ enviado_a: email.trim() }),
      }))
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo registrar la entrega.') }
    finally { setBusy('') }
  }

  async function resendReport() {
    if (!order) return
    setBusy('reenviar'); setError('')
    try {
      await api(`/ordenes/${order.id}/reenviar/`, {
        method: 'POST', body: JSON.stringify({ enviado_a: resendEmail.trim(), solicitud: crypto.randomUUID() }),
      })
      setResendEmail('')
      await api<{ results: EnvioReporte[] }>(`/ordenes/${order.id}/envios/`)
        .then(data => setHistory(data.results))
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo reenviar el reporte.') }
    finally { setBusy('') }
  }

  async function registerPayment() {    if (!order) return
    setBusy('pago'); setError('')
    try {
      await api('/pagos/', {
        method: 'POST',
        body: JSON.stringify({
          orden: order.id,
          monto: payAmount.trim(),
          forma_pago: payMethod,
          observacion: payNote.trim(),
        }),
      })
      setPayAmount(''); setPayNote('')
      setRetry(n => n + 1)
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo registrar el pago.') }
    finally { setBusy('') }
  }

  async function annulPayment(paymentId: number, orderNumber: string) {
    const motivo = window.prompt(`Motivo de la anulación del pago de ${orderNumber}:`)
    if (motivo === null) return
    if (!motivo.trim()) { setError('Indique el motivo de la anulación.'); return }
    setBusy('anular'); setError('')
    try {
      await api(`/pagos/${paymentId}/anular/`, {
        method: 'POST', body: JSON.stringify({ motivo: motivo.trim() }),
      })
      setRetry(n => n + 1)
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo anular el pago.') }
    finally { setBusy('') }
  }

  const updateDraft = (itemId: number, field: 'resultado' | 'bandera', value: string) =>
    setDrafts(current => {
      const existing = current[itemId] ?? { resultado: '', bandera: '', banderaManual: false }
      const next = field === 'resultado'
        ? { ...existing, resultado: value }
        // Editar la bandera a mano le da prioridad sobre el calculo automatico;
        // vaciarla devuelve el control al sistema.
        : { ...existing, bandera: value, banderaManual: value.trim() !== '' }
      return { ...current, [itemId]: next }
    })

  return <>
    <div className="page-heading">
      <div><p className="eyebrow">ORDEN</p><h1>{order?.numero ?? 'Detalle de orden'}</h1>
        {order && <p>{order.paciente_nombre || 'Sin paciente'} · {order.cliente_nombre || 'Particular'}</p>}</div>
      <button className="secondary" onClick={onBack}>Volver al listado</button>
    </div>
    {error && <div className="error" role="alert">{error} <button className="secondary" onClick={() => { setOrder(null); setError(''); setRetry(n => n + 1) }}>Reintentar</button></div>}
    {!order && !error && <p role="status" className="empty">Cargando orden…</p>}
    {order && <>
      <section className="panel detail-panel">
        <dl className="detail-grid">
          <div><dt>Estado</dt><dd><span className={`badge ${order.estado}`}>{orderStates[order.estado] || order.estado}</span></dd></div>
          <div><dt>Fecha</dt><dd>{order.fecha}</dd></div>
          <div><dt>Paciente</dt><dd>{order.paciente_nombre || 'Sin paciente'}</dd></div>
          <div><dt>Cliente</dt><dd>{order.cliente_nombre || 'Particular'}</dd></div>
          <div><dt>Solicitado por</dt><dd>{order.solicitado_por || 'Sin dato'}</dd></div>
          <div><dt>Total</dt><dd>{order.total === null ? <span className="warning">Tarifa pendiente</span> : money(order.total)}</dd></div>
          <div><dt>Pagado</dt><dd>{money(order.total_pagado ?? '0')}</dd></div>
          <div><dt>Saldo</dt><dd>{order.saldo === null ? <span className="warning">Sin total</span>
            : Number(order.saldo) > 0 ? <span className="warning">{money(order.saldo)}</span> : money(order.saldo)}</dd></div>
        </dl>
      </section>
      <section className="panel detail-panel">
        <h2>Estudios</h2>
        {order.items.length === 0 ? <p className="empty">La orden no tiene estudios.</p> : <div className="table-scroll">
          <table><thead><tr><th>Estudio</th><th>Cantidad</th><th>Medición</th><th>Resultado</th><th>Referencia</th><th>Bandera</th></tr></thead>
            <tbody>{order.items.map(item => {
              const manual = drafts[item.id]?.banderaManual ?? item.bandera_manual
              // Lo que el sistema va a calcular al guardar, si el laboratorio no define la bandera.
              const sugerencia = !manual && item.bandera_calculada ? item.bandera_calculada : ''
              return <tr key={item.id}>
              <td><strong>{item.paquete ? item.paquete_nombre : `${item.examen_codigo} — ${item.examen_nombre}`}</strong>
                {item.paquete && <small>{item.examen_codigo} — {item.examen_nombre}</small>}</td>
              <td>{item.cantidad}</td>
              <td>{measurements[item.medicion] || item.medicion}</td>
              <td>{editable
                ? <input aria-label={`Resultado ${item.examen_codigo}`} className="result-input" maxLength={100}
                  value={drafts[item.id]?.resultado ?? ''} onChange={e => updateDraft(item.id, 'resultado', e.target.value)} />
                : item.resultado || 'Pendiente'}</td>
              <td className="ref-cell">{referenceText(item) || '—'}</td>
              <td>{editable
                ? <input aria-label={`Bandera ${item.examen_codigo}`} className="flag-input" maxLength={5}
                  placeholder={sugerencia}
                  title={sugerencia ? `El sistema calcula: ${sugerencia}` : undefined}
                  value={drafts[item.id]?.bandera ?? ''} onChange={e => updateDraft(item.id, 'bandera', e.target.value)} />
                : item.bandera || '—'}
                {item.rango_estado !== 'sin_rango' && <span className={`badge rango ${item.rango_estado}`}>
                  {rangeLabels[item.rango_estado]}
                  {manual && ' · manual'}
                </span>}
                {item.validado_at && <span className="badge validada">Validado</span>}</td>
            </tr>})}</tbody></table>
        </div>}
        {editable ? <div className="form-actions">
          <button disabled={busy !== ''} onClick={saveResults}>{busy === 'resultados' ? 'Guardando…' : 'Guardar resultados'}</button>
          {canValidate && <button className="secondary" disabled={!complete || busy !== ''} onClick={() => send('validar')}>{busy === 'validar' ? 'Validando…' : 'Validar resultados'}</button>}
        </div> : <p className="empty">La orden ya está cerrada y no admite cambios.</p>}
        {(order.estado === 'validada' || order.reporte) && <div className="form-actions">
          {order.estado === 'validada' && canReport && <button disabled={busy !== ''} onClick={generateReport}>{busy === 'reporte' ? 'Generando…' : 'Generar reporte'}</button>}
          {order.reporte && <a className="button-link" href={order.reporte.pdf_url}>Descargar PDF {order.reporte.numero}</a>}
        </div>}
      </section>
      {(order.estado === 'pdf' && order.reporte && canReport) || order.estado === 'entregada' ? <section className="panel detail-panel">
        <h2>Entrega</h2>
        {order.estado === 'entregada' ? <p>
          Entregada{order.reporte?.entregado_at ? ` el ${new Date(order.reporte.entregado_at).toLocaleString('es-PE')}` : ''}
          {order.reporte?.enviado_a ? ` por correo a ${order.reporte.enviado_a}` : ' en mano'}
          {order.reporte?.entregado_por ? ` · registrada por ${order.reporte.entregado_por}` : ''}.
        </p> : <>
          <p>Envíe el informe por correo o registre la entrega en mano.</p>
          <div className="delivery-form">
            <label>Correo de entrega (opcional)
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="paciente@correo.com" />
            </label>
            <button disabled={busy !== ''} onClick={registerDelivery}>
              {busy === 'entrega' ? 'Registrando…' : email.trim() ? 'Enviar y entregar' : 'Registrar entrega'}
            </button>
          </div>
        </>}
      </section> : null}
      {order.reporte && canReport ? <section className="panel detail-panel">
        <h2>Historial de envíos</h2>
        {history.length === 0 && order.estado !== 'entregada' ? <p className="empty">Sin envíos registrados.</p> : <div className="table-scroll">
          <table><thead><tr><th>Fecha</th><th>Destinatario</th><th>Estado</th><th>Registrado por</th><th>Reenvío</th></tr></thead>
            <tbody>{history.map(e => <tr key={e.id}>
              <td>{new Date(e.fecha).toLocaleString('es-PE')}</td>
              <td>{e.enviado_a}</td>
              <td><span className={`badge ${e.estado}`}>{e.estado}</span></td>
              <td>{e.usuario}</td>
              <td>{e.reenvio ? 'Sí' : 'No'}</td>
            </tr>)}</tbody></table>
        </div>}
        {order.estado === 'entregada' && <div className="delivery-form" style={{marginTop: '12px'}}>
          <label>Nuevo correo de entrega (opcional)
            <input type="email" value={resendEmail} onChange={e => setResendEmail(e.target.value)} placeholder="otro@correo.com" />
          </label>
          <button disabled={busy !== ''} onClick={resendReport}>
            {busy === 'reenviar' ? 'Reenviando…' : resendEmail.trim() ? 'Reenviar por correo' : 'Reenviar en mano'}
          </button>
        </div>}
      </section> : null}
      <section className="panel detail-panel">
        <h2>Pagos</h2>
        {(order.pagos ?? []).length === 0 ? <p className="empty">Esta orden no tiene pagos registrados.</p> : <div className="table-scroll">
          <table><thead><tr><th>Fecha</th><th>Monto</th><th>Forma</th><th>Registrado por</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>{(order.pagos ?? []).map(p => <tr key={p.id}>
              <td>{new Date(p.fecha).toLocaleString('es-PE')}</td>
              <td>{money(p.monto)}</td>
              <td>{paymentMethods[p.forma_pago] || p.forma_pago}</td>
              <td>{p.registrado_por_nombre || '—'}</td>
              <td>{p.anulado
                ? <span className="badge anulado" title={p.motivo_anulacion}>Anulado</span>
                : <span className="badge validada">Vigente</span>}</td>
              <td>{canPay && !p.anulado
                ? <button className="secondary" disabled={busy !== ''} onClick={() => annulPayment(p.id, order.numero)}>Anular</button>
                : null}</td>
            </tr>)}</tbody></table>
        </div>}
        {canPay && order.total !== null && <div className="delivery-form" style={{marginTop: '12px'}}>
          <label>Monto del pago
            <input type="number" min="0.01" step="0.01" value={payAmount}
              onChange={e => setPayAmount(e.target.value)} placeholder="0.00" />
          </label>
          <label>Forma de pago
            <select value={payMethod} onChange={e => setPayMethod(e.target.value)}>
              {Object.entries(paymentMethods).map(([key, title]) => <option key={key} value={key}>{title}</option>)}
            </select>
          </label>
          <label>Observación
            <input value={payNote} onChange={e => setPayNote(e.target.value)} maxLength={200} />
          </label>
          <button disabled={busy !== '' || !payAmount.trim()} onClick={registerPayment}>
            {busy === 'pago' ? 'Registrando…' : 'Registrar pago'}
          </button>
        </div>}
      </section>
      <section className="panel detail-panel">
        <h2>Observación</h2>
        <p>{order.observacion || 'Sin observaciones.'}</p>
      </section>
    </>}
  </>
}
