import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { allPages, api } from '../api/client'
import type { AccountStatement, Customer, Order, Payment } from '../api/types'
import { money, paymentMethods } from '../api/types'
import { puede } from '../api/permisos'

type Props = { role: string; orders: Order[]; onOpenOrder: (id: number) => void }

export default function Payments({ role, orders, onOpenOrder }: Props) {
  const [payments, setPayments] = useState<Payment[]>([])
  const [statement, setStatement] = useState<AccountStatement[]>([])
  const [clients, setClients] = useState<Customer[]>([])
  const [clientFilter, setClientFilter] = useState('')
  const [methodFilter, setMethodFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const canRegister = puede(role, 'pagos.registrar')
  const canAnnul = puede(role, 'pagos.anular')

  function currentQuery() {
    const query = new URLSearchParams()
    if (clientFilter) query.set('cliente', clientFilter)
    if (methodFilter) query.set('forma_pago', methodFilter)
    if (statusFilter) query.set('anulado', statusFilter)
    return query.toString() ? `?${query.toString()}` : ''
  }

  async function cargar(suffix: string) {
    const [lista, cuenta, clientes] = await Promise.all([
      allPages<Payment>(`/pagos/${suffix}`),
      api<AccountStatement[]>('/pagos/estado-cuenta/'),
      allPages<Customer>('/clientes/'),
    ])
    setPayments(lista)
    setStatement(cuenta)
    setClients(clientes)
  }

  useEffect(() => {
    let cancelled = false
    const query = new URLSearchParams()
    if (clientFilter) query.set('cliente', clientFilter)
    if (methodFilter) query.set('forma_pago', methodFilter)
    if (statusFilter) query.set('anulado', statusFilter)
    const suffix = query.toString() ? `?${query.toString()}` : ''
    Promise.all([
      allPages<Payment>(`/pagos/${suffix}`),
      api<AccountStatement[]>('/pagos/estado-cuenta/'),
      allPages<Customer>('/clientes/'),
    ])
      .then(([lista, cuenta, clientes]) => {
        if (cancelled) return
        setPayments(lista)
        setStatement(cuenta)
        setClients(clientes)
      })
      .catch(e => { if (!cancelled) setError(e instanceof Error ? e.message : 'No se pudieron cargar los pagos.') })
    return () => { cancelled = true }
  }, [clientFilter, methodFilter, statusFilter])

  async function registrar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const orden = String(data.get('orden') ?? '')
    const monto = String(data.get('monto') ?? '').trim()
    if (!orden) { setError('Elegí la orden del pago.'); return }
    setBusy(true); setError('')
    try {
      await api('/pagos/', {
        method: 'POST',
        body: JSON.stringify({
          orden: Number(orden),
          monto,
          forma_pago: String(data.get('forma_pago') ?? 'contado'),
          observacion: String(data.get('observacion') ?? '').trim(),
        }),
      })
      event.currentTarget.reset()
      await cargar(currentQuery())
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo registrar el pago.') }
    finally { setBusy(false) }
  }

  async function anular(payment: Payment) {
    const motivo = window.prompt(`Motivo de la anulación del pago de ${payment.orden_numero}:`)
    if (motivo === null) return
    if (!motivo.trim()) { setError('Indique el motivo de la anulación.'); return }
    setBusy(true); setError('')
    try {
      await api(`/pagos/${payment.id}/anular/`, {
        method: 'POST', body: JSON.stringify({ motivo: motivo.trim() }),
      })
      await cargar(currentQuery())
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo anular el pago.') }
    finally { setBusy(false) }
  }

  return <>
    <div className="page-heading">
      <div><p className="eyebrow">CAJA</p><h1>Pagos</h1>
        <p>Registre los cobros y revise el saldo pendiente por cliente.</p></div>
    </div>
    {error && <div className="error" role="alert">{error}</div>}

    {canRegister && <section className="panel form-panel">
      <h2>Registrar pago</h2>
      <form onSubmit={registrar}>
        <div className="field-grid">
          <label>Orden<select name="orden" required defaultValue="">
            <option value="" disabled>Seleccione la orden</option>
            {orders.map(o => <option key={o.id} value={o.id}>{o.numero} — {o.cliente_nombre || 'Particular'}</option>)}
          </select></label>
          <label>Monto<input name="monto" type="number" min="0.01" step="0.01" required /></label>
          <label>Forma de pago<select name="forma_pago" defaultValue="contado">
            {Object.entries(paymentMethods).map(([key, title]) => <option key={key} value={key}>{title}</option>)}
          </select></label>
          <label>Observación<input name="observacion" maxLength={200} /></label>
        </div>
        <div className="form-actions">
          <button disabled={busy}>Registrar pago</button>
        </div>
      </form>
    </section>}

    <section className="panel detail-panel">
      <h2>Estado de cuenta</h2>
      {statement.length === 0 ? <p className="empty">Sin órdenes facturadas todavía.</p> : <div className="table-scroll">
        <table><thead><tr><th>Cliente</th><th>Facturado</th><th>Pagado</th><th>Saldo</th></tr></thead>
          <tbody>{statement.map(row => <tr key={row.cliente_id ?? 0}>
            <td><strong>{row.cliente}</strong></td>
            <td>{money(row.facturado)}</td>
            <td>{money(row.pagado)}</td>
            <td className={Number(row.saldo) > 0 ? 'warning' : undefined}>{money(row.saldo)}</td>
          </tr>)}</tbody></table>
      </div>}
    </section>

    <section className="panel detail-panel">
      <h2>Pagos registrados</h2>
      <div className="filters">
        <label>Cliente<select value={clientFilter} onChange={e => setClientFilter(e.target.value)}>
          <option value="">Todos</option>
          {clients.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
        </select></label>
        <label>Forma de pago<select value={methodFilter} onChange={e => setMethodFilter(e.target.value)}>
          <option value="">Todas</option>
          {Object.entries(paymentMethods).map(([key, title]) => <option key={key} value={key}>{title}</option>)}
        </select></label>
        <label>Estado<select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">Todos</option>
          <option value="false">Vigentes</option>
          <option value="true">Anulados</option>
        </select></label>
      </div>
      {payments.length === 0 ? <p className="empty">No hay pagos registrados.</p> : <div className="table-scroll">
        <table><thead><tr><th>Fecha</th><th>Orden</th><th>Cliente</th><th>Monto</th><th>Forma</th><th>Registrado por</th><th>Estado</th><th>Acciones</th></tr></thead>
          <tbody>{payments.map(p => <tr key={p.id}>
            <td>{new Date(p.fecha).toLocaleString('es-PE')}</td>
            <td><button className="link-button" onClick={() => onOpenOrder(p.orden)}>{p.orden_numero}</button></td>
            <td>{p.orden_cliente}</td>
            <td>{money(p.monto)}</td>
            <td>{paymentMethods[p.forma_pago] || p.forma_pago}</td>
            <td>{p.registrado_por_nombre || '—'}</td>
            <td>{p.anulado
              ? <span className="badge anulado" title={p.motivo_anulacion}>Anulado</span>
              : <span className="badge validada">Vigente</span>}</td>
            <td>{canAnnul && !p.anulado
              ? <button className="secondary" disabled={busy} onClick={() => anular(p)}>Anular</button>
              : null}</td>
          </tr>)}</tbody></table>
      </div>}
      {payments.length > 0 && <p className="table-footer">{payments.length} pagos</p>}
    </section>
  </>
}
