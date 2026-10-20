import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { OrderDetail as Order } from '../api/types'
import { money, orderStates } from '../api/types'

const measurements: Record<string, string> = { unica: 'Única', pre_post: 'Pre y post' }

export default function OrderDetail({ id, onBack }: { id: number; onBack: () => void }) {
  const [order, setOrder] = useState<Order | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    api<Order>(`/ordenes/${id}/`, { signal: controller.signal })
      .then(setOrder)
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
    return () => controller.abort()
  }, [id, retry])

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
        </dl>
      </section>
      <section className="panel detail-panel">
        <h2>Estudios</h2>
        {order.items.length === 0 ? <p className="empty">La orden no tiene estudios.</p> : <div className="table-scroll">
          <table><thead><tr><th>Estudio</th><th>Cantidad</th><th>Medición</th><th>Resultado</th></tr></thead>
            <tbody>{order.items.map(item => <tr key={item.id}>
              <td><strong>{item.paquete ? item.paquete_nombre : `${item.examen_codigo} — ${item.examen_nombre}`}</strong>
                {item.paquete && <small>{item.examen_codigo} — {item.examen_nombre}</small>}</td>
              <td>{item.cantidad}</td>
              <td>{measurements[item.medicion] || item.medicion}</td>
              <td>{item.resultado || 'Pendiente'}{item.bandera && <span className="badge">{item.bandera}</span>}</td>
            </tr>)}</tbody></table>
        </div>}
      </section>
      <section className="panel detail-panel">
        <h2>Observación</h2>
        <p>{order.observacion || 'Sin observaciones.'}</p>
      </section>
    </>}
  </>
}
