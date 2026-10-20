import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { allPages, api, setCsrfToken } from './api/client'
import type { Order, Session } from './api/types'
import { money, orderStates } from './api/types'
import Catalog from './components/Catalog'
import Clients from './components/Clients'
import OrderDetail from './components/OrderDetail'
import OrderForm from './components/OrderForm'
import Patients from './components/Patients'
import Tariffs from './components/Tariffs'
import './App.css'

type View = { kind: 'list' } | { kind: 'form'; key: number } | { kind: 'detail'; id: number } | { kind: 'patients' } | { kind: 'clients' } | { kind: 'catalog' } | { kind: 'tariffs' }
export default function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [orders, setOrders] = useState<Order[]>([])
  const [view, setView] = useState<View>({ kind: 'list' })
  const nextDraft = useRef(0)
  const [query, setQuery] = useState('')
  const [state, setState] = useState('')
  const [date, setDate] = useState('')
  const [revision, refresh] = useState(0)
  const userId = session?.user?.id

  function acceptSession(value: Session) {
    setCsrfToken(value.csrf_token)
    setSession(value)
  }
  useEffect(() => {
    const controller = new AbortController()
    api<Session>('/auth/session/', { signal: controller.signal })
      .then(acceptSession)
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [])
  useEffect(() => {
    if (!userId) return
    const controller = new AbortController()
    allPages<Order>('/ordenes/', controller.signal)
      .then(setOrders)
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [userId, revision])

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    setBusy(true); setError('')
    try {
      // Bootstrap again after a failed connection or an expired CSRF cookie.
      acceptSession(await api<Session>('/auth/session/'))
      setLoading(true)
      acceptSession(await api<Session>('/auth/login/', {
        method: 'POST', body: JSON.stringify({ username: data.get('username'), password: data.get('password') }),
      }))
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión.') }
    finally { setBusy(false); setLoading(false) }
  }
  async function logout() {
    setBusy(true); setError('')
    try {
      acceptSession(await api<Session>('/auth/logout/', { method: 'POST' }))
      setOrders([]); setView({ kind: 'list' })
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo cerrar sesión.') }
    finally { setBusy(false) }
  }

  if (!session?.user) return <main className="login-page">
    <section className="login-intro"><span className="brand-mark">LC</span><h1>LabCore</h1>
      <p>Sistema de gestión para laboratorio clínico</p><h2>Menos tareas repetitivas.<br />Más atención a cada paciente.</h2>
      <p>Órdenes, pacientes y tarifas en un solo lugar.</p></section>
    <form className="login-card" onSubmit={login}><p className="eyebrow">ACCESO AL LABORATORIO</p>
      <h2>Bienvenido de nuevo</h2><p>Ingrese con su cuenta del laboratorio.</p>
      {error && <p role="alert" className="error">{error}</p>}
      <label>Usuario<input name="username" autoComplete="username" required /></label>
      <label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label>
      <button disabled={busy || loading}>{busy ? 'Ingresando…' : 'Iniciar sesión'}</button>
      {loading && <p role="status">Comprobando sesión…</p>}
    </form>
  </main>

  const visible = orders.filter(o => (!state || o.estado === state) && (!date || o.fecha === date)
    && `${o.numero} ${o.paciente_nombre} ${o.cliente_nombre}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()))
  const ordersActive = view.kind === 'list' || view.kind === 'form' || view.kind === 'detail'
  return <div className="workspace">
    <aside className="sidebar"><div className="brand"><span className="brand-mark">LC</span><strong>LabCore</strong></div>
      <p className="eyebrow">LABORATORIO CLÍNICO</p><nav aria-label="Principal">
        <button className={ordersActive ? 'nav-active' : ''} onClick={() => setView({ kind: 'list' })}>Órdenes</button>
        <button className={view.kind === 'patients' ? 'nav-active' : ''} onClick={() => setView({ kind: 'patients' })}>Pacientes</button>
        <button className={view.kind === 'clients' ? 'nav-active' : ''} onClick={() => setView({ kind: 'clients' })}>Clientes</button>
        <button className={view.kind === 'catalog' ? 'nav-active' : ''} onClick={() => setView({ kind: 'catalog' })}>Catálogo</button>
        <button className={view.kind === 'tariffs' ? 'nav-active' : ''} onClick={() => setView({ kind: 'tariffs' })}>Tarifarios</button>
      </nav>
      <p className="sidebar-note">Espacio de trabajo<br />Recepción y laboratorio</p></aside>
    <div className="workspace-main"><header className="topbar"><span>Gestión de órdenes</span><div><strong>{session.user.name}</strong><small>{session.user.role}</small></div><button className="secondary" disabled={busy} onClick={logout}>Cerrar sesión</button></header>
      <main className="content">{error && <div role="alert" className="error">{error} <button className="secondary" onClick={() => { setError(''); refresh(n => n + 1) }}>Reintentar</button></div>}
        {view.kind === 'tariffs' ? <Tariffs />
          : view.kind === 'catalog' ? <Catalog />
          : view.kind === 'clients' ? <Clients />
          : view.kind === 'patients' ? <Patients />
          : view.kind === 'form' ? <OrderForm key={view.key} onCancel={() => setView({ kind: 'list' })}
          onSaved={() => { setView(current => current.kind === 'form' && current.key === view.key ? { kind: 'list' } : current); refresh(n => n + 1) }} />
          : view.kind === 'detail' ? <OrderDetail key={view.id} id={view.id} onBack={() => setView({ kind: 'list' })} />
          : <>
          <div className="page-heading"><div><p className="eyebrow">RECEPCIÓN</p><h1>Órdenes de laboratorio</h1><p>Consulte el estado y registre nuevas solicitudes.</p></div><button onClick={() => setView({ kind: 'form', key: ++nextDraft.current })}>Nueva orden</button></div>
          <div className="stats"><article><span>Órdenes registradas</span><strong>{orders.length}</strong></article><article><span>Pendientes de iniciar</span><strong>{orders.filter(o => o.estado === 'registrada').length}</strong></article><article><span>Sin total disponible</span><strong>{orders.filter(o => o.total === null).length}</strong></article></div>
          <section className="panel"><div className="filters"><label>Buscar<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Número, paciente o cliente" /></label><label>Estado<select value={state} onChange={e => setState(e.target.value)}><option value="">Todos</option>{Object.entries(orderStates).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label><label>Fecha<input type="date" value={date} onChange={e => setDate(e.target.value)} /></label></div>
            {loading ? <p role="status" className="empty">Cargando órdenes…</p> : <><div className="table-scroll"><table><thead><tr><th>Orden</th><th>Paciente</th><th>Cliente</th><th>Fecha</th><th>Estado</th><th>Total</th><th>Acciones</th></tr></thead><tbody>{visible.map(o => <tr key={o.id}><td><strong>{o.numero}</strong></td><td>{o.paciente_nombre || 'Sin paciente'}</td><td>{o.cliente_nombre || 'Particular'}</td><td>{o.fecha}</td><td><span className={`badge ${o.estado}`}>{orderStates[o.estado] || o.estado}</span></td><td>{o.total === null ? <span className="warning">Tarifa pendiente</span> : money(o.total)}</td><td><button className="secondary" aria-label={`Ver orden ${o.numero}`} onClick={() => setView({ kind: 'detail', id: o.id })}>Ver</button></td></tr>)}</tbody></table></div>{visible.length === 0 && <p className="empty">No hay órdenes para mostrar.</p>}<p className="table-footer">{visible.length} de {orders.length} órdenes</p></>}
          </section></>}
      </main>
    </div>
  </div>
}
