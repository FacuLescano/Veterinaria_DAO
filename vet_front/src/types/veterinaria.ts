export type Especie = 'Canino' | 'Felino' | 'Otro';
export type SexoMascota = 'Macho' | 'Hembra';

export interface Responsable {
  id: string;
  nombreCompleto: string;
  documento: string; // DNI o CUIT
  telefono: string;
  email: string;
  domicilio: string;
  fechaAlta: string;
}

export interface Mascota {
  id: string;
  responsableId: string;
  nombre: string;
  especie: Especie;
  raza: string;
  sexo: SexoMascota;
  fechaNacimientoAprox: string;
  pesoKg: number;
  alergias?: string;
  fotoUrl?: string;
}

export type EstadoTurno = 'Pendiente' | 'Confirmado' | 'Atendido' | 'Cancelado' | 'Ausente';

export interface Turno {
  id: string;
  mascotaId: string;
  responsableId: string;
  veterinarioId?: string;
  veterinario: string;
  fecha: string;
  hora: string;
  motivo: string;
  estado: EstadoTurno;
}

export interface ConsultaMedica {
  id: string;
  mascotaId: string;
  veterinario: string;
  fecha: string;
  hora: string;
  motivo: string;
  evaluacionClinica: string;
  diagnosticoPresuntivo: string;
  tratamiento: string;
  vacunaAplicada?: string;
  requiereAnalisis: boolean;
  turnoId?: string;
}

export type TipoAnalisis = 
  | 'Hemograma Completo'
  | 'Perfil Bioquímico Hepático'
  | 'Perfil Renal (Urea y Creatinina)'
  | 'Orina Completa y Sedimento'
  | 'Coproparasitológico Seriado'
  | 'Citología Cutánea / PAAF'
  | 'Dosaje Hormonal (T4 / Cortisol)';

export type EstadoOrden = 'Solicitada' | 'En preparación' | 'Enviada' | 'Con resultados' | 'Cancelada';

export interface DetalleAnalisis {
  id: string;
  tipoAnalisis: TipoAnalisis;
  indicaciones: string;
  muestraAsociadaId?: string;
  estado: 'Pendiente de muestra' | 'Muestra vinculada' | 'En proceso' | 'Resultado listo';
}

export interface OrdenAnalisis {
  id: string; // Ej: ORD-2026-001
  consultaId: string;
  mascotaId: string;
  veterinarioSolicitante: string;
  fechaSolicitud: string;
  prioridad: 'Normal' | 'Urgente';
  estado: EstadoOrden;
  detalles: DetalleAnalisis[];
}

export type TipoMaterialBiologico = 
  | 'Sangre con EDTA (Tubo lila)'
  | 'Suero sanguíneo (Tubo rojo)'
  | 'Plasma heparinizado'
  | 'Orina por cistocentesis'
  | 'Materia fecal'
  | 'Biopsia / Tejido en formol'
  | 'Raspado cutáneo';

export type CondicionConservacion = 'Refrigerada (2° a 8°C)' | 'Congelada (-20°C)' | 'Temperatura Ambiente (15° a 25°C)';

export type EstadoMuestra = 
  | 'Extraída'
  | 'Empaquetada'
  | 'En tránsito'
  | 'Recibida'
  | 'Analizada'
  | 'Rechazada';

export interface EventoTrazabilidad {
  id: string;
  fechaHora: string;
  estadoAnterior?: EstadoMuestra;
  estadoNuevo: EstadoMuestra;
  responsable: string;
  ubicacion: string;
  observaciones?: string;
}

export interface MuestraBiologica {
  id: string; // Ej: MUE-8921
  ordenId: string;
  identificacionFisica: string; // Código de tubo
  tipoMaterial: TipoMaterialBiologico;
  fechaHoraExtraccion: string;
  responsableExtraccion: string;
  condicionConservacion: CondicionConservacion;
  estadoActual: EstadoMuestra;
  conservadoraId?: string;
  remitoId?: string;
  historialTrazabilidad: EventoTrazabilidad[];
  motivoRechazo?: string;
  observaciones?: string;
}

export interface Conservadora {
  id: string; // Ej: CON-01
  nombre: string;
  capacidadMuestras: number;
  temperaturaRequerida: string;
  disponible: boolean;
}

export type EstadoPrecinto = 'Integro' | 'Roto' | 'Ausente' | 'CodigoNoCoincide';

export interface PrecintoSanitario {
  id: string;
  codigoUnico: string; // Ej: PREC-48921
  conservadoraId: string;
  colocadoPor: string;
  fechaHoraColocacion: string;
  estadoVerificacion?: EstadoPrecinto;
  verificadoPor?: string;
  fechaHoraVerificacion?: string;
  observaciones?: string;
}

export type EstadoEnvio = 'En preparación' | 'Despachado' | 'Recibido' | 'Con incidencias';

export interface RemitoBiologico {
  id: string; // Ej: REM-2026-104
  envioId?: string;
  numeroRemito?: string;
  fechaEmision: string;
  clinicaOrigen: string;
  laboratorioDestino: string;
  responsableDespacho: string;
  transportista: string;
  conservadoraId: string;
  precintoCodigo: string;
  muestrasIds: string[];
  estado: EstadoEnvio;
  temperaturaDespachoC: number;
  observaciones?: string;
}

export interface Incidencia {
  id: string;
  fechaHora: string;
  remitoId?: string;
  muestraId?: string;
  tipo: 'Precinto Roto' | 'Temperatura Fuera de Rango' | 'Muestra Insuficiente' | 'Retraso en Transporte' | 'Discrepancia en Remito';
  descripcion: string;
  responsableReporte: string;
  resuelto: boolean;
  resolucion?: string;
}

export interface ResultadoAnalisis {
  id: string;
  ordenId: string;
  detalleAnalisisId: string;
  muestraId: string;
  fechaRecepcionResultado: string;
  laboratorioNombre: string;
  valores: {
    parametro: string;
    valor: string;
    unidad: string;
    rangoReferencia: string;
    alerta?: 'Normal' | 'Alto' | 'Bajo';
  }[];
  conclusionDiagnostica: string;
  nombreArchivoAdjunto?: string;
  estado: 'Recibido' | 'En revisión' | 'Validado por Veterinario';
  validadoPor?: string;
}
