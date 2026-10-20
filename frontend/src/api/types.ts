export type User = { id: number; username: string; name: string; role: string }
export type Session = { user: User | null; csrf_token: string }
export type Patient = { id: number; dni: string | null; apellidos: string; nombres: string; sexo: string | null; fecha_nacimiento: string | null; cliente: number | null; observaciones: string; nombre_completo: string }
export type Zone = { id: number; nombre: string; activo: boolean }
export type Customer = { id: number; nombre: string; tipo: string; zona: number | null; contacto: string; activo: boolean }
export type Exam = { id: number; codigo: string; nombre: string; area: string; resultado_tipo: string; unidad: string; metodo: string; ref_min: string | null; ref_max: string | null; ref_texto: string; mide_pre_post: boolean; activo: boolean }
export type Package = { id: number; nombre: string; frecuencia: string; activo: boolean; examenes: { orden: number; examen: number }[] }
export type ExamTariff = { id: number; examen: number; examen_codigo: string; examen_nombre: string; precio: string; zona: number | null; zona_nombre: string | null; cliente: number | null; cliente_nombre: string | null; vigencia_desde: string | null; activo: boolean }
export type PackageTariff = { id: number; paquete: number; paquete_nombre: string; precio: string; zona: number | null; zona_nombre: string | null; cliente: number | null; cliente_nombre: string | null; vigencia_desde: string | null; activo: boolean }
export type OrderReport = { id: number; numero: string; generado: string; pdf_url: string; enviado_a: string; entregado_at: string | null; entregado_por: string | null }
export type Order = { id: number; numero: string; paciente_nombre: string; cliente_nombre: string; fecha: string; estado: string; total: string | null }
export type OrderItem = { id: number; examen: number; examen_codigo: string; examen_nombre: string; paquete: number | null; paquete_nombre: string; cantidad: number; medicion: string; resultado: string; bandera: string; validado_por: number | null; validado_at: string | null }
export type OrderDetail = Order & { observacion: string; solicitado_por: string; items: OrderItem[]; reporte: OrderReport | null }
export type Item = { examen: number; paquete?: number; cantidad: number; medicion: string }
export type Quote = { items: { precio_unitario: string; subtotal: string }[]; total: string }
export const money = (value: string) => new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(Number(value))
export const orderStates: Record<string, string> = { registrada: 'Registrada', en_proceso: 'En proceso', resultada: 'Con resultados', validada: 'Validada', pdf: 'PDF generado', entregada: 'Entregada' }
