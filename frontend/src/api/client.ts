const API_BASE = '/api'

let csrfToken = ''
export function setCsrfToken(token: string) { csrfToken = token }

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function errorText(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(errorText).filter(Boolean).join(' · ')
  if (value && typeof value === 'object') {
    if ('detail' in value) return errorText((value as { detail: unknown }).detail)
    return Object.entries(value).map(([key, item]) => `${key}: ${errorText(item)}`).join(' · ')
  }
  return ''
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (csrfToken && options.method && !['GET', 'HEAD'].includes(options.method.toUpperCase())) {
    headers.set('X-CSRFToken', csrfToken)
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'same-origin',
    headers,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, errorText(body) || `No se pudo completar la solicitud (${res.status}).`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] }

export async function allPages<T>(path: string, signal?: AbortSignal): Promise<T[]> {
  const results: T[] = []
  let next: string | null = path
  const visited = new Set<string>()
  while (next) {
    if (visited.has(next)) throw new Error('La paginación de la API se repitió.')
    visited.add(next)
    const page: Page<T> = await api<Page<T>>(next, { signal })
    results.push(...page.results)
    if (page.next) {
      const url = new URL(page.next, window.location.origin)
      if (!url.pathname.startsWith('/api/')) throw new Error('Paginación inválida.')
      next = url.pathname.slice(4) + url.search
    } else next = null
  }
  return results
}
