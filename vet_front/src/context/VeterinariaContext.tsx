import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  Responsable,
  Mascota,
  Turno,
  ConsultaMedica,
  OrdenAnalisis,
  MuestraBiologica,
  Conservadora,
  RemitoBiologico,
  PrecintoSanitario,
  Incidencia,
  ResultadoAnalisis,
  EstadoTurno,
  EstadoPrecinto,
  EstadoMuestra
} from '../types/veterinaria';
import {
  INITIAL_RESPONSABLES,
  INITIAL_MASCOTAS,
  INITIAL_TURNOS,
  INITIAL_CONSULTAS,
  INITIAL_ORDENES,
  INITIAL_MUESTRAS,
  INITIAL_CONSERVADORAS,
  INITIAL_PRECINTOS,
  INITIAL_REMITOS,
  INITIAL_INCIDENCIAS,
  INITIAL_RESULTADOS
} from '../data/mockData';

export type ActiveModule = 'pacientes' | 'ordenes' | 'despacho' | 'recepcion' | 'python';

interface ToastMessage {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  description?: string;
}

interface VeterinariaContextType {
  responsables: Responsable[];
  mascotas: Mascota[];
  turnos: Turno[];
  consultas: ConsultaMedica[];
  ordenes: OrdenAnalisis[];
  muestras: MuestraBiologica[];
  conservadoras: Conservadora[];
  precintos: PrecintoSanitario[];
  remitos: RemitoBiologico[];
  incidencias: Incidencia[];
  resultados: ResultadoAnalisis[];
  
  // Navigation & UI state
  activeModule: ActiveModule;
  setActiveModule: (module: ActiveModule) => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void;
  isMobileMenuOpen: boolean;
  setIsMobileMenuOpen: (open: boolean) => void;
  selectedMascotaId: string | null;
  setSelectedMascotaId: (id: string | null) => void;
  toast: ToastMessage | null;
  showToast: (toast: Omit<ToastMessage, 'id'>) => void;
  clearToast: () => void;

  // Actions
  addResponsable: (resp: Omit<Responsable, 'id' | 'fechaAlta'>) => Responsable;
  addMascota: (mascota: Omit<Mascota, 'id'>) => Mascota;
  updateMascota: (id: string, updates: Partial<Mascota>) => void;
  addTurno: (turno: Omit<Turno, 'id'>) => { success: boolean; error?: string };
  updateTurnoEstado: (id: string, nuevoEstado: EstadoTurno) => void;
  addConsulta: (consulta: Omit<ConsultaMedica, 'id'>) => ConsultaMedica;
  createOrden: (orden: Omit<OrdenAnalisis, 'id'>) => OrdenAnalisis;
  registrarMuestra: (muestra: Omit<MuestraBiologica, 'id' | 'historialTrazabilidad' | 'estadoActual'>) => MuestraBiologica;
  vincularMuestraConAnalisis: (ordenId: string, detalleId: string, muestraId: string) => void;
  prepararEnvio: (params: {
    conservadoraId: string;
    precintoCodigo: string;
    responsableDespacho: string;
    transportista: string;
    muestrasIds: string[];
    temperaturaDespachoC: number;
    observaciones?: string;
  }) => RemitoBiologico;
  verificarPrecintoYRecepcion: (params: {
    remitoId: string;
    estadoPrecinto: EstadoPrecinto;
    verificadoPor: string;
    observaciones?: string;
  }) => void;
  registrarResultado: (resultado: Omit<ResultadoAnalisis, 'id'>) => ResultadoAnalisis;
  resolverIncidencia: (id: string, resolucion: string) => void;
  resetToDemoData: () => void;
}

const VeterinariaContext = createContext<VeterinariaContextType | undefined>(undefined);

const STORAGE_KEY = 'patitas_veterinaria_data_v2';

export const VeterinariaProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Load saved data or defaults
  const [responsables, setResponsables] = useState<Responsable[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_responsables`) || localStorage.getItem('patitas_veterinaria_data_v1_responsables');
    return saved ? JSON.parse(saved) : INITIAL_RESPONSABLES;
  });

  const [mascotas, setMascotas] = useState<Mascota[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_mascotas`) || localStorage.getItem('patitas_veterinaria_data_v1_mascotas');
    if (saved) {
      try {
        const parsed: Mascota[] = JSON.parse(saved);
        return parsed.map(m => {
          const initial = INITIAL_MASCOTAS.find(init => init.id === m.id);
          if (initial) {
            return {
              ...m,
              raza: (m.id === 'MASC-002' && initial.raza === 'Mestizo') ? initial.raza : m.raza,
              fotoUrl: m.fotoUrl || initial.fotoUrl
            };
          }
          return m;
        });
      } catch {
        return INITIAL_MASCOTAS;
      }
    }
    return INITIAL_MASCOTAS;
  });

  const [turnos, setTurnos] = useState<Turno[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_turnos`);
    return saved ? JSON.parse(saved) : INITIAL_TURNOS;
  });

  const [consultas, setConsultas] = useState<ConsultaMedica[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_consultas`);
    return saved ? JSON.parse(saved) : INITIAL_CONSULTAS;
  });

  const [ordenes, setOrdenes] = useState<OrdenAnalisis[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_ordenes`);
    return saved ? JSON.parse(saved) : INITIAL_ORDENES;
  });

  const [muestras, setMuestras] = useState<MuestraBiologica[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_muestras`);
    return saved ? JSON.parse(saved) : INITIAL_MUESTRAS;
  });

  const [conservadoras, setConservadoras] = useState<Conservadora[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_conservadoras`);
    return saved ? JSON.parse(saved) : INITIAL_CONSERVADORAS;
  });

  const [precintos, setPrecintos] = useState<PrecintoSanitario[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_precintos`);
    return saved ? JSON.parse(saved) : INITIAL_PRECINTOS;
  });

  const [remitos, setRemitos] = useState<RemitoBiologico[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_remitos`);
    return saved ? JSON.parse(saved) : INITIAL_REMITOS;
  });

  const [incidencias, setIncidencias] = useState<Incidencia[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_incidencias`);
    return saved ? JSON.parse(saved) : INITIAL_INCIDENCIAS;
  });

  const [resultados, setResultados] = useState<ResultadoAnalisis[]>(() => {
    const saved = localStorage.getItem(`${STORAGE_KEY}_resultados`);
    return saved ? JSON.parse(saved) : INITIAL_RESULTADOS;
  });

  // UI state
  const [activeModule, setActiveModule] = useState<ActiveModule>('pacientes');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [selectedMascotaId, setSelectedMascotaId] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const showToast = (t: Omit<ToastMessage, 'id'>) => {
    setToast({ ...t, id: Date.now().toString() });
  };

  const clearToast = () => setToast(null);

  // Sync to localStorage
  useEffect(() => {
    localStorage.setItem(`${STORAGE_KEY}_responsables`, JSON.stringify(responsables));
    localStorage.setItem(`${STORAGE_KEY}_mascotas`, JSON.stringify(mascotas));
    localStorage.setItem(`${STORAGE_KEY}_turnos`, JSON.stringify(turnos));
    localStorage.setItem(`${STORAGE_KEY}_consultas`, JSON.stringify(consultas));
    localStorage.setItem(`${STORAGE_KEY}_ordenes`, JSON.stringify(ordenes));
    localStorage.setItem(`${STORAGE_KEY}_muestras`, JSON.stringify(muestras));
    localStorage.setItem(`${STORAGE_KEY}_conservadoras`, JSON.stringify(conservadoras));
    localStorage.setItem(`${STORAGE_KEY}_precintos`, JSON.stringify(precintos));
    localStorage.setItem(`${STORAGE_KEY}_remitos`, JSON.stringify(remitos));
    localStorage.setItem(`${STORAGE_KEY}_incidencias`, JSON.stringify(incidencias));
    localStorage.setItem(`${STORAGE_KEY}_resultados`, JSON.stringify(resultados));
  }, [responsables, mascotas, turnos, consultas, ordenes, muestras, conservadoras, precintos, remitos, incidencias, resultados]);

  // ACTIONS

  const addResponsable = (data: Omit<Responsable, 'id' | 'fechaAlta'>): Responsable => {
    const newId = `RESP-${String(responsables.length + 1).padStart(3, '0')}`;
    const newResp: Responsable = {
      ...data,
      id: newId,
      fechaAlta: new Date().toISOString().split('T')[0]
    };
    setResponsables(prev => [newResp, ...prev]);
    showToast({
      type: 'success',
      title: 'Responsable registrado',
      description: `${newResp.nombreCompleto} ha sido registrado exitosamente.`
    });
    return newResp;
  };

  const addMascota = (data: Omit<Mascota, 'id'>): Mascota => {
    const newId = `MASC-${String(mascotas.length + 1).padStart(3, '0')}`;
    const newMascota: Mascota = {
      ...data,
      id: newId
    };
    setMascotas(prev => [newMascota, ...prev]);
    showToast({
      type: 'success',
      title: 'Mascota registrada',
      description: `${newMascota.nombre} ya tiene su ficha en la clínica.`
    });
    return newMascota;
  };

  const updateMascota = (id: string, updates: Partial<Mascota>) => {
    setMascotas(prev => prev.map(m => (m.id === id ? { ...m, ...updates } : m)));
    showToast({
      type: 'success',
      title: 'Ficha médica actualizada',
      description: 'Los cambios del paciente se guardaron correctamente.'
    });
  };

  const addTurno = (data: Omit<Turno, 'id'>): { success: boolean; error?: string } => {
    // Regla de Negocio: Evitar superposición de turnos para el mismo profesional y fecha/hora
    const conflicto = turnos.find(
      t => t.veterinario === data.veterinario &&
           t.fecha === data.fecha &&
           t.hora === data.hora &&
           t.estado !== 'Cancelado'
    );

    if (conflicto) {
      const err = `El profesional ${data.veterinario} ya tiene un turno reservado el ${data.fecha} a las ${data.hora}.`;
      showToast({
        type: 'error',
        title: 'Superposición de turnos',
        description: err
      });
      return { success: false, error: err };
    }

    const newId = `TUR-${String(turnos.length + 101)}`;
    const newTurno: Turno = {
      ...data,
      id: newId
    };
    setTurnos(prev => [newTurno, ...prev]);
    showToast({
      type: 'success',
      title: 'Turno agendado',
      description: `Turno agendado para el ${data.fecha} a las ${data.hora}.`
    });
    return { success: true };
  };

  const updateTurnoEstado = (id: string, nuevoEstado: EstadoTurno) => {
    setTurnos(prev => prev.map(t => t.id === id ? { ...t, estado: nuevoEstado } : t));
    showToast({
      type: 'info',
      title: 'Estado de turno actualizado',
      description: `El turno pasó a estado ${nuevoEstado}.`
    });
  };

  const addConsulta = (data: Omit<ConsultaMedica, 'id'>): ConsultaMedica => {
    const newId = `CON-${String(consultas.length + 1).padStart(3, '0')}`;
    const newConsulta: ConsultaMedica = {
      ...data,
      id: newId
    };
    setConsultas(prev => [newConsulta, ...prev]);

    // If it was linked to a turno, mark the turno as Atendido
    if (data.turnoId) {
      setTurnos(prev => prev.map(t => t.id === data.turnoId ? { ...t, estado: 'Atendido' } : t));
    }

    showToast({
      type: 'success',
      title: 'Consulta médica guardada',
      description: `Se registró la atención para ${mascotas.find(m => m.id === data.mascotaId)?.nombre || 'el paciente'}.`
    });
    return newConsulta;
  };

  const createOrden = (data: Omit<OrdenAnalisis, 'id'>): OrdenAnalisis => {
    const newId = `ORD-2026-${String(ordenes.length + 1).padStart(3, '0')}`;
    const newOrden: OrdenAnalisis = {
      ...data,
      id: newId
    };
    setOrdenes(prev => [newOrden, ...prev]);
    showToast({
      type: 'success',
      title: 'Orden de derivación creada',
      description: `Se formalizó la orden ${newId} con ${data.detalles.length} análisis.`
    });
    return newOrden;
  };

  const registrarMuestra = (
    data: Omit<MuestraBiologica, 'id' | 'historialTrazabilidad' | 'estadoActual'>
  ): MuestraBiologica => {
    const newId = `MUE-${Math.floor(1000 + Math.random() * 9000)}`;
    const nuevoEvento = {
      id: `TRAZ-${Date.now()}`,
      fechaHora: new Date().toISOString().replace('T', ' ').substring(0, 16),
      estadoNuevo: 'Extraída' as EstadoMuestra,
      responsable: data.responsableExtraccion,
      ubicacion: 'Consultorio Clínico - Extracción',
      observaciones: data.observaciones || 'Extracción y rotulado inicial del tubo.'
    };

    const newMuestra: MuestraBiologica = {
      ...data,
      id: newId,
      estadoActual: 'Extraída',
      historialTrazabilidad: [nuevoEvento]
    };

    setMuestras(prev => [newMuestra, ...prev]);
    
    // Update orden state if needed
    setOrdenes(prev => prev.map(o => o.id === data.ordenId && o.estado === 'Solicitada' ? { ...o, estado: 'En preparación' } : o));

    showToast({
      type: 'success',
      title: 'Muestra biológica registrada',
      description: `Identificador ${newId} (${data.identificacionFisica}) registrado con trazabilidad de origen.`
    });
    return newMuestra;
  };

  const vincularMuestraConAnalisis = (ordenId: string, detalleId: string, muestraId: string) => {
    setOrdenes(prev => prev.map(ord => {
      if (ord.id !== ordenId) return ord;
      return {
        ...ord,
        detalles: ord.detalles.map(det => {
          if (det.id !== detalleId) return det;
          return {
            ...det,
            muestraAsociadaId: muestraId,
            estado: 'Muestra vinculada'
          };
        })
      };
    }));

    showToast({
      type: 'info',
      title: 'Muestra vinculada al análisis',
      description: `La muestra ${muestraId} fue asociada al análisis solicitado.`
    });
  };

  const prepararEnvio = (params: {
    conservadoraId: string;
    precintoCodigo: string;
    responsableDespacho: string;
    transportista: string;
    muestrasIds: string[];
    temperaturaDespachoC: number;
    observaciones?: string;
  }): RemitoBiologico => {
    const now = new Date().toISOString().replace('T', ' ').substring(0, 16);
    const remitoId = `REM-2026-${String(remitos.length + 13).padStart(3, '0')}`;
    const precintoId = `PREC-${Date.now().toString().slice(-5)}`;

    // 1. Register Precinto
    const nuevoPrecinto: PrecintoSanitario = {
      id: precintoId,
      codigoUnico: params.precintoCodigo,
      conservadoraId: params.conservadoraId,
      colocadoPor: params.responsableDespacho,
      fechaHoraColocacion: now
    };
    setPrecintos(prev => [nuevoPrecinto, ...prev]);

    // 2. Register Remito
    const nuevoRemito: RemitoBiologico = {
      id: remitoId,
      fechaEmision: now,
      clinicaOrigen: 'Clínica Veterinaria Patitas & Co. - Sede Central',
      laboratorioDestino: 'Laboratorio Central de Derivación BioVet',
      responsableDespacho: params.responsableDespacho,
      transportista: params.transportista,
      conservadoraId: params.conservadoraId,
      precintoCodigo: params.precintoCodigo,
      muestrasIds: params.muestrasIds,
      estado: 'Despachado',
      temperaturaDespachoC: params.temperaturaDespachoC,
      observaciones: params.observaciones
    };
    setRemitos(prev => [nuevoRemito, ...prev]);

    // 3. Mark Conservadora as in-use
    setConservadoras(prev => prev.map(c => c.id === params.conservadoraId ? { ...c, disponible: false } : c));

    // 4. Update state of samples: Extraída -> Empaquetada -> En tránsito
    setMuestras(prev => prev.map(m => {
      if (!params.muestrasIds.includes(m.id)) return m;
      const eventosNuevos = [
        ...m.historialTrazabilidad,
        {
          id: `TRAZ-${Date.now()}-1`,
          fechaHora: now,
          estadoAnterior: m.estadoActual,
          estadoNuevo: 'Empaquetada' as EstadoMuestra,
          responsable: params.responsableDespacho,
          ubicacion: `Conservadora ${params.conservadoraId} (Precinto ${params.precintoCodigo})`,
          observaciones: 'Colocación en conservadora con geles refrigerantes.'
        },
        {
          id: `TRAZ-${Date.now()}-2`,
          fechaHora: now,
          estadoAnterior: 'Empaquetada' as EstadoMuestra,
          estadoNuevo: 'En tránsito' as EstadoMuestra,
          responsable: params.transportista,
          ubicacion: 'En traslado hacia Laboratorio Central BioVet',
          observaciones: `Despachado con remito ${remitoId}. T° inicial: ${params.temperaturaDespachoC}°C.`
        }
      ];

      return {
        ...m,
        conservadoraId: params.conservadoraId,
        remitoId: remitoId,
        estadoActual: 'En tránsito' as EstadoMuestra,
        historialTrazabilidad: eventosNuevos
      };
    }));

    // Update related ordenes to Enviada
    setOrdenes(prev => prev.map(ord => {
      const hasSample = ord.detalles.some(d => d.muestraAsociadaId && params.muestrasIds.includes(d.muestraAsociadaId));
      return hasSample ? { ...ord, estado: 'Enviada' } : ord;
    }));

    showToast({
      type: 'success',
      title: 'Envío despachado con éxito',
      description: `Remito ${remitoId} generado con ${params.muestrasIds.length} muestras. Precinto ${params.precintoCodigo}.`
    });

    return nuevoRemito;
  };

  const verificarPrecintoYRecepcion = (params: {
    remitoId: string;
    estadoPrecinto: EstadoPrecinto;
    verificadoPor: string;
    observaciones?: string;
  }) => {
    const now = new Date().toISOString().replace('T', ' ').substring(0, 16);
    const targetRemito = remitos.find(r => r.id === params.remitoId);
    if (!targetRemito) return;

    const esPrecintoValido = params.estadoPrecinto === 'Integro';

    // 1. Update Precinto record
    setPrecintos(prev => prev.map(p => {
      if (p.codigoUnico === targetRemito.precintoCodigo) {
        return {
          ...p,
          estadoVerificacion: params.estadoPrecinto,
          verificadoPor: params.verificadoPor,
          fechaHoraVerificacion: now,
          observaciones: params.observaciones
        };
      }
      return p;
    }));

    // 2. Free up Conservadora
    setConservadoras(prev => prev.map(c => c.id === targetRemito.conservadoraId ? { ...c, disponible: true } : c));

    if (esPrecintoValido) {
      // SUCCESSFUL RECEIPT
      setRemitos(prev => prev.map(r => r.id === params.remitoId ? { ...r, estado: 'Recibido' } : r));

      setMuestras(prev => prev.map(m => {
        if (!targetRemito.muestrasIds.includes(m.id)) return m;
        return {
          ...m,
          estadoActual: 'Recibida',
          historialTrazabilidad: [
            ...m.historialTrazabilidad,
            {
              id: `TRAZ-${Date.now()}`,
              fechaHora: now,
              estadoAnterior: m.estadoActual,
              estadoNuevo: 'Recibida',
              responsable: params.verificadoPor,
              ubicacion: 'Laboratorio Central BioVet - Recepción y Triaje',
              observaciones: `Precinto ${targetRemito.precintoCodigo} ÍNTEGRO. Remito verificado. ${params.observaciones || ''}`
            }
          ]
        };
      }));

      showToast({
        type: 'success',
        title: 'Recepción validada con precinto íntegro',
        description: `Se confirmó la llegada de las muestras al laboratorio en condiciones óptimas.`
      });
    } else {
      // REJECTED - CRITICAL BUSINESS RULE!
      // "Impedir el procesamiento de muestras si el precinto sanitario llega roto (cambio de estado a Muestra Rechazada)"
      setRemitos(prev => prev.map(r => r.id === params.remitoId ? { ...r, estado: 'Con incidencias' } : r));

      const motivoFalla = params.estadoPrecinto === 'Roto' 
        ? 'Precinto sanitario roto / vulnerado en transporte. Pérdida de cadena de custodia biológica.'
        : params.estadoPrecinto === 'CodigoNoCoincide'
        ? 'Código de precinto no coincide con el remito biológico despachado.'
        : 'Precinto sanitario ausente.';

      // Register Incident
      const nuevaIncidencia: Incidencia = {
        id: `INC-${Date.now().toString().slice(-4)}`,
        fechaHora: now,
        remitoId: params.remitoId,
        tipo: 'Precinto Roto',
        descripcion: `${motivoFalla}. Observaciones: ${params.observaciones || 'Sin detalles adicionales'}.`,
        responsableReporte: params.verificadoPor,
        resuelto: false
      };
      setIncidencias(prev => [nuevaIncidencia, ...prev]);

      // Mutate samples to RECHAZADA
      setMuestras(prev => prev.map(m => {
        if (!targetRemito.muestrasIds.includes(m.id)) return m;
        return {
          ...m,
          estadoActual: 'Rechazada',
          motivoRechazo: motivoFalla,
          historialTrazabilidad: [
            ...m.historialTrazabilidad,
            {
              id: `TRAZ-${Date.now()}`,
              fechaHora: now,
              estadoAnterior: m.estadoActual,
              estadoNuevo: 'Rechazada',
              responsable: params.verificadoPor,
              ubicacion: 'Laboratorio Central BioVet - Control de Ingreso',
              observaciones: `RECHAZO BIOLÓGICO: ${motivoFalla}`
            }
          ]
        };
      }));

      showToast({
        type: 'error',
        title: '¡Muestras rechazadas por precinto!',
        description: `Regla de seguridad: ${motivoFalla} Se bloqueó el procesamiento y se registró la incidencia.`
      });
    }
  };

  const registrarResultado = (data: Omit<ResultadoAnalisis, 'id'>): ResultadoAnalisis => {
    const newId = `RES-${Date.now().toString().slice(-4)}`;
    const newResultado: ResultadoAnalisis = {
      ...data,
      id: newId
    };
    setResultados(prev => [newResultado, ...prev]);

    // Update Muestra to Analizada
    setMuestras(prev => prev.map(m => {
      if (m.id !== data.muestraId) return m;
      return {
        ...m,
        estadoActual: 'Analizada',
        historialTrazabilidad: [
          ...m.historialTrazabilidad,
          {
            id: `TRAZ-${Date.now()}`,
            fechaHora: data.fechaRecepcionResultado,
            estadoAnterior: m.estadoActual,
            estadoNuevo: 'Analizada',
            responsable: data.laboratorioNombre,
            ubicacion: 'Laboratorio Central BioVet - Análisis Finalizado',
            observaciones: `Resultado emitido y validado (${newResultado.conclusionDiagnostica}).`
          }
        ]
      };
    }));

    // Update DetalleAnalisis to Resultado listo
    setOrdenes(prev => prev.map(ord => {
      if (ord.id !== data.ordenId) return ord;
      const updatedDetalles = ord.detalles.map(d => {
        if (d.id === data.detalleAnalisisId) {
          return { ...d, estado: 'Resultado listo' as const };
        }
        return d;
      });
      // Check if all are done
      const allDone = updatedDetalles.every(d => d.estado === 'Resultado listo');
      return {
        ...ord,
        detalles: updatedDetalles,
        estado: allDone ? ('Con resultados' as const) : ord.estado
      };
    }));

    showToast({
      type: 'success',
      title: 'Resultado de análisis cargado',
      description: `Se incorporó el informe del laboratorio a la historia clínica del paciente.`
    });

    return newResultado;
  };

  const resolverIncidencia = (id: string, resolucion: string) => {
    setIncidencias(prev => prev.map(inc => inc.id === id ? { ...inc, resuelto: true, resolucion } : inc));
    showToast({
      type: 'info',
      title: 'Incidencia resuelta',
      description: 'Se registró la resolución y acciones correctivas tomadas.'
    });
  };

  const resetToDemoData = () => {
    setResponsables(INITIAL_RESPONSABLES);
    setMascotas(INITIAL_MASCOTAS);
    setTurnos(INITIAL_TURNOS);
    setConsultas(INITIAL_CONSULTAS);
    setOrdenes(INITIAL_ORDENES);
    setMuestras(INITIAL_MUESTRAS);
    setConservadoras(INITIAL_CONSERVADORAS);
    setPrecintos(INITIAL_PRECINTOS);
    setRemitos(INITIAL_REMITOS);
    setIncidencias(INITIAL_INCIDENCIAS);
    setResultados(INITIAL_RESULTADOS);
    localStorage.clear();
    showToast({
      type: 'info',
      title: 'Datos restaurados',
      description: 'Se restablecieron los datos iniciales de demostración de Patitas & Co.'
    });
  };

  return (
    <VeterinariaContext.Provider
      value={{
        responsables,
        mascotas,
        turnos,
        consultas,
        ordenes,
        muestras,
        conservadoras,
        precintos,
        remitos,
        incidencias,
        resultados,
        activeModule,
        setActiveModule,
        isSidebarCollapsed,
        setIsSidebarCollapsed,
        isMobileMenuOpen,
        setIsMobileMenuOpen,
        selectedMascotaId,
        setSelectedMascotaId,
        toast,
        showToast,
        clearToast,
        addResponsable,
        addMascota,
        updateMascota,
        addTurno,
        updateTurnoEstado,
        addConsulta,
        createOrden,
        registrarMuestra,
        vincularMuestraConAnalisis,
        prepararEnvio,
        verificarPrecintoYRecepcion,
        registrarResultado,
        resolverIncidencia,
        resetToDemoData
      }}
    >
      {children}
    </VeterinariaContext.Provider>
  );
};

export const useVeterinaria = () => {
  const context = useContext(VeterinariaContext);
  if (!context) {
    throw new Error('useVeterinaria debe utilizarse dentro de un VeterinariaProvider');
  }
  return context;
};

// Aliases para compatibilidad
export const VeterinaryProvider = VeterinariaProvider;
export const useVeterinary = useVeterinaria;
