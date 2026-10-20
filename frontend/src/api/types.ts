export type User = { id: number; username: string; name: string; role: string }
export type Session = { user: User | null; csrf_token: string }
export type Patient = { id: number; nombre_completo: string; cliente: number | null }
export type Customer = { id: number; nombre: string }
export type Exam = { id: number; codigo: string; nombre: string; activo: boolean }
export type Package = { id: number; nombre: string; activo: boolean; examenes: { orden: number; examen: number }[] }
export type Order = { id: number; numero: string; paciente_nombre: string; cliente_nombre: string; fecha: string; estado: string; total: string | null }
export type OrderItem = { id: number; examen: number; examen_codigo: string; examen_nombre: string; paquete: number | null; paquete_nombre: string; cantidad: number; medicion: string; resultado: string; bandera: string }
export type OrderDetail = Order & { observacion: string; solicitado_por: string; items: OrderItem[] }
export type Item = { examen: number; paquete?: number; cantidad: number; medicion: string }
export type Quote = { items: { precio_unitario: string; subtotal: string }[]; total: string }
export const money = (value: string) => new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(Number(value))
export const orderStates: Record<string, string> = { registrada: 'Registrada', en_proceso: 'En proceso', resultada: 'Con resultados', validada: 'Validada', pdf: 'PDF generado', entregada: 'Entregada' }
