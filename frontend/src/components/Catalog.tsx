import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { allPages, api } from '../api/client'
import type { Exam, Package } from '../api/types'

const areas: Record<string, string> = { sangre: 'Sangre', aguas: 'Aguas' }
const resultTypes: Record<string, string> = { numerico: 'Numérico', texto: 'Texto' }
const frequencies: Record<string, string> = { mensual: 'Mensual', bimestral: 'Bimestral', trimestral: 'Trimestral', semestral: 'Semestral' }

type Editor = { kind: 'exam'; value?: Exam } | { kind: 'package'; value?: Package }

function ExamForm({ exam, onCancel, onSaved }: { exam?: Exam; onCancel: () => void; onSaved: () => void }) {
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
      await api(exam ? `/examenes/${exam.id}/` : '/examenes/', {
        method: exam ? 'PATCH' : 'POST', body: JSON.stringify(payload),
      })
      onSaved()
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar el examen.') }
    finally { setBusy(false) }
  }

  return <form className="panel form-panel" onSubmit={submit}>
    <h2>{exam ? 'Editar examen' : 'Datos del examen'}</h2>
    <div className="field-grid">
      <label>Código<input name="codigo" required maxLength={30} defaultValue={exam?.codigo ?? ''} /></label>
      <label>Nombre<input name="nombre" required maxLength={200} defaultValue={exam?.nombre ?? ''} /></label>
      <label>Área<select name="area" defaultValue={exam?.area ?? 'sangre'}>{Object.entries(areas).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
      <label>Tipo de resultado<select name="resultado_tipo" defaultValue={exam?.resultado_tipo ?? 'numerico'}>{Object.entries(resultTypes).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
      <label>Unidad<input name="unidad" maxLength={30} defaultValue={exam?.unidad ?? ''} /></label>
      <label>Método<input name="metodo" maxLength={100} defaultValue={exam?.metodo ?? ''} /></label>
      <label>Mínimo<input name="ref_min" type="number" step="0.0001" defaultValue={exam?.ref_min ?? ''} /></label>
      <label>Máximo<input name="ref_max" type="number" step="0.0001" defaultValue={exam?.ref_max ?? ''} /></label>
      <label>Texto de referencia<input name="ref_texto" maxLength={200} defaultValue={exam?.ref_texto ?? ''} /></label>
    </div>
    <div className="checks">
      <label className="check"><input type="checkbox" name="mide_pre_post" defaultChecked={exam?.mide_pre_post ?? false} /> Mide pre y post</label>
      <label className="check"><input type="checkbox" name="activo" defaultChecked={exam ? exam.activo : true} /> Examen activo</label>
    </div>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="form-actions">
      <button disabled={busy}>{busy ? 'Guardando…' : exam ? 'Guardar cambios' : 'Guardar examen'}</button>
      <button type="button" className="secondary" disabled={busy} onClick={onCancel}>Cancelar</button>
    </div>
  </form>
}

function PackageForm({ exams, pkg, onCancel, onSaved }: {
  exams: Exam[]
  pkg?: Package
  onCancel: () => void
  onSaved: () => void
}) {
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
      await api(pkg ? `/paquetes/${pkg.id}/` : '/paquetes/', {
        method: pkg ? 'PATCH' : 'POST', body: JSON.stringify(payload),
      })
      onSaved()
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar el paquete.') }
    finally { setBusy(false) }
  }

  const member = (id: number) => pkg?.examenes.some(item => item.examen === id) ?? false

  return <form className="panel form-panel" onSubmit={submit}>
    <h2>{pkg ? 'Editar paquete' : 'Datos del paquete'}</h2>
    <div className="field-grid">
      <label>Nombre<input name="nombre" required maxLength={100} defaultValue={pkg?.nombre ?? ''} /></label>
      <label>Frecuencia<select name="frecuencia" defaultValue={pkg?.frecuencia ?? 'mensual'}>{Object.entries(frequencies).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
    </div>
    <fieldset className="member-picker">
      <legend>Exámenes del paquete</legend>
      {exams.map(e => <label key={e.id} className="check"><input type="checkbox" name="examen" value={e.id} defaultChecked={member(e.id)} /> {e.codigo} - {e.nombre}</label>)}
    </fieldset>
    <label className="check"><input type="checkbox" name="activo" defaultChecked={pkg ? pkg.activo : true} /> Paquete activo</label>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="form-actions">
      <button disabled={busy}>{busy ? 'Guardando…' : pkg ? 'Guardar cambios' : 'Guardar paquete'}</button>
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
  const [editor, setEditor] = useState<Editor | null>(null)
  const [revision, refresh] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([allPages<Exam>('/examenes/', controller.signal), allPages<Package>('/paquetes/', controller.signal)])
      .then(([foundExams, foundPackages]) => { setExams(foundExams); setPackages(foundPackages) })
      .catch(e => { if (!controller.signal.aborted) setError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [revision])

  async function remove(path: string, label: string) {
    if (!window.confirm(`¿Eliminar ${label}?`)) return
    try {
      await api(`/${path}/`, { method: 'DELETE' })
      refresh(n => n + 1)
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo eliminar el registro.') }
  }

  const text = query.toLocaleLowerCase()
  const visibleExams = exams.filter(e => `${e.codigo} ${e.nombre}`.toLocaleLowerCase().includes(text))
  const visiblePackages = packages.filter(p => p.nombre.toLocaleLowerCase().includes(text))

  return <>
    <div className="page-heading"><div><p className="eyebrow">CATÁLOGO</p><h1>Catálogo</h1><p>Exámenes y paquetes disponibles para las órdenes.</p></div>
      {!editor && <button onClick={() => setEditor({ kind: tab === 'exams' ? 'exam' : 'package' })}>{tab === 'exams' ? 'Nuevo examen' : 'Nuevo paquete'}</button>}</div>
    {error && <div className="error" role="alert">{error} <button className="secondary" onClick={() => { setError(''); refresh(n => n + 1) }}>Reintentar</button></div>}
    {editor?.kind === 'exam' ? <ExamForm exam={editor.value} onCancel={() => setEditor(null)} onSaved={() => { setEditor(null); refresh(n => n + 1) }} />
      : editor?.kind === 'package' ? <PackageForm exams={exams} pkg={editor.value} onCancel={() => setEditor(null)} onSaved={() => { setEditor(null); refresh(n => n + 1) }} />
      : <>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === 'exams'} className={tab === 'exams' ? 'nav-active' : ''} onClick={() => setTab('exams')}>Exámenes</button>
        <button role="tab" aria-selected={tab === 'packages'} className={tab === 'packages' ? 'nav-active' : ''} onClick={() => setTab('packages')}>Paquetes</button>
      </div>
      <section className="panel">
        <div className="filters"><label>Buscar<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Código o nombre" /></label></div>
        {loading ? <p role="status" className="empty">Cargando catálogo…</p> : tab === 'exams' ? <>
          <div className="table-scroll"><table><thead><tr><th>Código</th><th>Nombre</th><th>Área</th><th>Tipo</th><th>Unidad</th><th>Estado</th><th></th></tr></thead>
            <tbody>{visibleExams.map(e => <tr key={e.id}><td><strong>{e.codigo}</strong></td><td>{e.nombre}</td><td>{areas[e.area] || e.area}</td><td>{resultTypes[e.resultado_tipo] || e.resultado_tipo}</td><td>{e.unidad || '—'}</td><td><span className={`badge ${e.activo ? 'validada' : ''}`}>{e.activo ? 'Activo' : 'Inactivo'}</span></td>
              <td className="row-actions"><button className="link" onClick={() => setEditor({ kind: 'exam', value: e })}>Editar</button><button className="link danger" onClick={() => remove(`examenes/${e.id}`, `el examen ${e.codigo}`)}>Eliminar</button></td></tr>)}</tbody></table></div>
          {visibleExams.length === 0 && <p className="empty">No hay exámenes para mostrar.</p>}
          <p className="table-footer">{visibleExams.length} de {exams.length} exámenes</p></> : <>
          <div className="table-scroll"><table><thead><tr><th>Paquete</th><th>Frecuencia</th><th>Exámenes</th><th>Estado</th><th></th></tr></thead>
            <tbody>{visiblePackages.map(p => <tr key={p.id}><td><strong>{p.nombre}</strong></td><td>{frequencies[p.frecuencia] || p.frecuencia}</td><td>{p.examenes.length} exámenes</td><td><span className={`badge ${p.activo ? 'validada' : ''}`}>{p.activo ? 'Activo' : 'Inactivo'}</span></td>
              <td className="row-actions"><button className="link" onClick={() => setEditor({ kind: 'package', value: p })}>Editar</button><button className="link danger" onClick={() => remove(`paquetes/${p.id}`, `el paquete ${p.nombre}`)}>Eliminar</button></td></tr>)}</tbody></table></div>
          {visiblePackages.length === 0 && <p className="empty">No hay paquetes para mostrar.</p>}
          <p className="table-footer">{visiblePackages.length} de {packages.length} paquetes</p></>}
      </section></>}
  </>
}
