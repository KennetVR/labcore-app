/**
 * Capacidades que la interfaz usa para mostrar u ocultar controles.
 *
 * El servidor es la autoridad: esta tabla solo evita ofrecer acciones que la
 * API va a rechazar. Si cambia la política, primero cambia el backend.
 */

export const ADMIN = 'admin'
export const ENCARGADO = 'encargada'

export type Capacidad =
  | 'pacientes.editar'
  | 'pacientes.eliminar'
  | 'clientes.editar'
  | 'clientes.eliminar'
  | 'catalogo.editar'
  | 'tarifas.editar'
  | 'ordenes.editar'
  | 'ordenes.eliminar'
  | 'ordenes.reabrir'
  | 'resultados.capturar'
  | 'resultados.validar'
  | 'reportes.generar'
  | 'reportes.entregar'
  | 'reportes.reenviar'
  | 'reportes.ver'
  | 'pagos.registrar'
  | 'pagos.anular'

const OPERACION: Capacidad[] = [
  'pacientes.editar',
  'clientes.editar',
  'ordenes.editar',
  'resultados.capturar',
  'resultados.validar',
  'reportes.generar',
  'reportes.entregar',
  'reportes.reenviar',
  'reportes.ver',
  'pagos.registrar',
]

const CAPACIDADES: Record<string, Capacidad[]> = {
  [ADMIN]: [
    ...OPERACION,
    'pacientes.eliminar',
    'clientes.eliminar',
    'catalogo.editar',
    'tarifas.editar',
    'ordenes.eliminar',
    'ordenes.reabrir',
    'pagos.anular',
  ],
  [ENCARGADO]: OPERACION,
}

export function puede(role: string, capacidad: Capacidad): boolean {
  return (CAPACIDADES[role] ?? []).includes(capacidad)
}

export const roleLabels: Record<string, string> = {
  [ADMIN]: 'Administrador',
  [ENCARGADO]: 'Encargado',
}
