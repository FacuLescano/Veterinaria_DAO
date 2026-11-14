import React, { useState, useEffect, useMemo } from 'react';
import { 
  Stethoscope, 
  FlaskConical, 
  CheckCircle2, 
  AlertTriangle, 
  Mail, 
  FileSpreadsheet, 
  FileText, 
  RefreshCw, 
  Filter, 
  Search, 
  Calendar,
  CalendarCheck,
  CalendarX,
  X,
  Send,
  Loader2,
  TrendingUp,
  Award,
  ClipboardList
} from 'lucide-react';
import { useVeterinaria } from '../../../context/VeterinariaContext';
import { ReporteRendimientoClinicoResponse } from './types';

export const ReporteRendimientoClinico: React.FC = () => {
  const { showToast } = useVeterinaria();

  const [reporte3Data, setReporte3Data] = useState<ReporteRendimientoClinicoResponse | null>(null);
  const [cargando3, setCargando3] = useState(false);

  // Filtros
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [filtroVet, setFiltroVet] = useState('Todos');
  const [filtroEspecialidad, setFiltroEspecialidad] = useState('Todas');
  const [filtroEstadoTurno, setFiltroEstadoTurno] = useState('Todos');
  const [filtroDerivacion, setFiltroDerivacion] = useState('Todos');
  const [busquedaTabla, setBusquedaTabla] = useState('');

  // Modal Enviar por Correo
  const [modalEmailOpen, setModalEmailOpen] = useState(false);
  const [emailDestinatario, setEmailDestinatario] = useState('');
  const [asuntoEmail, setAsuntoEmail] = useState('');
  const [adjuntarPdf, setAdjuntarPdf] = useState(true);
  const [adjuntarExcel, setAdjuntarExcel] = useState(true);
  const [enviandoEmail, setEnviandoEmail] = useState(false);

  const cargarReporte3 = async () => {
    setCargando3(true);
    try {
      const params = new URLSearchParams();
      if (fechaDesde) params.append('fecha_desde', fechaDesde);
      if (fechaHasta) params.append('fecha_hasta', fechaHasta);
      if (filtroVet !== 'Todos') {
        params.append('veterinario', filtroVet);
        params.append('veterinario_nombre', filtroVet);
      }
      if (filtroEspecialidad !== 'Todas') {
        params.append('especialidad', filtroEspecialidad);
      }
      if (filtroEstadoTurno !== 'Todos') {
        params.append('estado_turno', filtroEstadoTurno);
      }
      if (filtroDerivacion !== 'Todos') {
        params.append('derivacion', filtroDerivacion);
      }

      const res = await fetch(`/api/v1/reportes/rendimiento-clinico?${params.toString()}`);
      if (!res.ok) throw new Error('Error al cargar reporte de rendimiento clínico');
      const data: ReporteRendimientoClinicoResponse = await res.json();
      setReporte3Data(data);
    } catch (err: any) {
      showToast({
        type: 'error',
        title: 'Error de carga',
        description: err.message || 'No se pudo conectar con el servicio de reportes clínicos'
      });
    } finally {
      setCargando3(false);
    }
  };

  useEffect(() => {
    void cargarReporte3();
  }, [filtroVet, filtroEspecialidad, filtroEstadoTurno, filtroDerivacion, fechaDesde, fechaHasta]);

  const descargarArchivo = async (formato: 'excel' | 'pdf') => {
    try {
      const params = new URLSearchParams();
      if (fechaDesde) params.append('fecha_desde', fechaDesde);
      if (fechaHasta) params.append('fecha_hasta', fechaHasta);
      if (filtroVet !== 'Todos') params.append('veterinario', filtroVet);
      if (filtroEspecialidad !== 'Todas') params.append('especialidad', filtroEspecialidad);
      if (filtroEstadoTurno !== 'Todos') params.append('estado_turno', filtroEstadoTurno);
      if (filtroDerivacion !== 'Todos') params.append('derivacion', filtroDerivacion);

      const endpoint = `/api/v1/reportes/rendimiento-clinico/${formato}?${params.toString()}`;
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`Error al generar ${formato.toUpperCase()}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = formato === 'excel' ? 'reporte_rendimiento_clinico.xlsx' : 'reporte_rendimiento_clinico.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showToast({
        type: 'success',
        title: 'Descarga completada',
        description: `Se descargó el archivo ${formato.toUpperCase()} de rendimiento clínico exitosamente.`
      });
    } catch (err: any) {
      showToast({
        type: 'error',
        title: 'Fallo en la descarga',
        description: err.message || 'No se pudo descargar el archivo.'
      });
    }
  };

  const enviarEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailDestinatario) return;

    setEnviandoEmail(true);
    try {
      const body = {
        destinatario: emailDestinatario,
        asunto: asuntoEmail || undefined,
        incluir_pdf: adjuntarPdf,
        incluir_excel: adjuntarExcel,
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
        veterinario: filtroVet !== 'Todos' ? filtroVet : undefined,
        especialidad: filtroEspecialidad !== 'Todas' ? filtroEspecialidad : undefined,
        estado_turno: filtroEstadoTurno !== 'Todos' ? filtroEstadoTurno : undefined,
        derivacion: filtroDerivacion !== 'Todos' ? filtroDerivacion : undefined,
      };

      const res = await fetch('/api/v1/reportes/rendimiento-clinico/enviar-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Fallo al despachar correo');

      showToast({
        type: 'success',
        title: 'Correo de Rendimiento enviado',
        description: data.mensaje || `El informe oficial fue enviado con éxito a ${emailDestinatario}.`
      });
      setModalEmailOpen(false);
    } catch (err: any) {
      showToast({
        type: 'error',
        title: 'Error de envío SMTP',
        description: err.message || 'No se pudo enviar el correo.'
      });
    } finally {
      setEnviandoEmail(false);
    }
  };

  const consultasFiltradas = useMemo(() => {
    if (!reporte3Data) return [];
    const term = busquedaTabla.trim().toLowerCase();
    if (!term) return reporte3Data.detalles_consultas;

    return reporte3Data.detalles_consultas.filter(d => 
      d.turno_id.toLowerCase().includes(term) ||
      d.paciente_nombre.toLowerCase().includes(term) ||
      d.tutor_nombre.toLowerCase().includes(term) ||
      d.veterinario_nombre.toLowerCase().includes(term) ||
      d.especialidad.toLowerCase().includes(term) ||
      d.motivo_consulta.toLowerCase().includes(term) ||
      d.diagnostico.toLowerCase().includes(term) ||
      d.estudios_solicitados.toLowerCase().includes(term)
    );
  }, [reporte3Data, busquedaTabla]);

  const kpis = reporte3Data?.kpis;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <img
            src="/assets/aistudio/Gemini_Generated_Image_o95dgio95dgio95d-removebg-preview_cbe90b76.png"
            alt="Logo Patitas & Co."
            className="w-11 h-11 object-contain"
          />
          <div>
            <h3 className="font-bold text-sm text-[#2D5864] leading-tight">
              PATITAS & CO. — RENDIMIENTO CLÍNICO Y TASA DE DERIVACIÓN MÉDICA
            </h3>
            <p className="text-xs text-neutral-500 mt-0.5">
              Reporte 3: Auditoría de Consultas, Ausentismo y Prescripción de Laboratorio
            </p>
          </div>
        </div>
        <div className="text-right hidden sm:block">
          <span className="text-[10px] font-mono text-neutral-400 block">Sede Central Córdoba</span>
          <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full font-semibold border border-emerald-200">
            Cuerpo Médico Activo · Gestión Clínica
          </span>
        </div>
      </div>

      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#2D5864]" />
            <span className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Filtros Clínicos:</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => void descargarArchivo('excel')}
              className="px-3 py-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs"
              title="Descargar libro Excel con tablas y formato"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Descargar Excel</span>
            </button>

            <button
              onClick={() => void descargarArchivo('pdf')}
              className="px-3 py-1.5 text-xs font-semibold text-rose-800 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs"
              title="Descargar informe oficial en PDF"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Descargar PDF</span>
            </button>

            <button
              onClick={() => setModalEmailOpen(true)}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <Mail className="w-3.5 h-3.5" />
              <span>Enviar por Correo</span>
            </button>

            <button
              onClick={() => void cargarReporte3()}
              disabled={cargando3}
              className="p-1.5 text-neutral-500 hover:text-[#2D5864] hover:bg-neutral-100 rounded-lg transition-colors"
              title="Actualizar datos"
            >
              <RefreshCw className={`w-4 h-4 ${cargando3 ? 'animate-spin text-[#2D5864]' : ''}`} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-2 border-t border-neutral-100 text-xs">
          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Médico Veterinario</label>
            <select
              value={filtroVet}
              onChange={(e) => setFiltroVet(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              {(reporte3Data?.filtros_disponibles.veterinarios || ['Todos']).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Especialidad</label>
            <select
              value={filtroEspecialidad}
              onChange={(e) => setFiltroEspecialidad(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              {(reporte3Data?.filtros_disponibles.especialidades || ['Todas']).map((esp) => (
                <option key={esp} value={esp}>{esp}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Derivación a Lab</label>
            <select
              value={filtroDerivacion}
              onChange={(e) => setFiltroDerivacion(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              {(reporte3Data?.filtros_disponibles.derivaciones || ['Todos', 'Con Derivación', 'Sin Derivación']).map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Estado de Cita</label>
            <select
              value={filtroEstadoTurno}
              onChange={(e) => setFiltroEstadoTurno(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              {(reporte3Data?.filtros_disponibles.estados_turno || ['Todos', 'Atendido', 'Ausente', 'Cancelado']).map((est) => (
                <option key={est} value={est}>{est}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Desde</label>
            <input
              type="date"
              value={fechaDesde}
              onChange={(e) => setFechaDesde(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Hasta</label>
            <input
              type="date"
              value={fechaHasta}
              onChange={(e) => setFechaHasta(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            />
          </div>
        </div>
      </div>

      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Agendados</span>
              <Calendar className="w-4 h-4 text-[#2D5864]" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-[#2D5864]">
                {kpis.total_turnos_agendados}
              </span>
              <span className="text-[10px] text-neutral-400">turnos</span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">100% de la agenda</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Atendidos</span>
              <CalendarCheck className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-emerald-700">
                {kpis.turnos_atendidos}
              </span>
              <span className="text-[10px] text-emerald-600 font-medium">
                ({kpis.tasa_asistencia_porcentaje}%)
              </span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">Efectividad de asistencia</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Ausentismo</span>
              <CalendarX className="w-4 h-4 text-rose-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className={`text-2xl font-bold ${kpis.tasa_ausentismo_porcentaje > 15 ? 'text-rose-700' : 'text-neutral-800'}`}>
                {kpis.tasa_ausentismo_porcentaje}%
              </span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">{kpis.turnos_ausentes} ausencias registradas</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Derivación Lab</span>
              <TrendingUp className="w-4 h-4 text-teal-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-teal-700">
                {kpis.tasa_derivacion_global_porcentaje}%
              </span>
              <span className="text-[10px] text-teal-600 font-medium">
                ({kpis.consultas_con_derivacion})
              </span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">De {kpis.turnos_atendidos} consultas</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Órdenes Lab</span>
              <FlaskConical className="w-4 h-4 text-[#2D5864]" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-[#2D5864]">
                {kpis.total_ordenes_laboratorio}
              </span>
              <span className="text-[10px] text-neutral-400">pedidos</span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">Prescripciones a central</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Determinaciones</span>
              <ClipboardList className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-indigo-800">
                {kpis.total_estudios_solicitados}
              </span>
              <span className="text-[10px] text-neutral-400 font-medium">análisis</span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">Prom. {kpis.promedio_estudios_por_orden} por orden</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-neutral-100">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-[#2D5864]" />
              <h4 className="font-bold text-sm text-[#2D5864]">
                Tasa de Derivación y Perfil por Profesional
              </h4>
            </div>
            <span className="text-[10px] text-neutral-400">Auditoría médica</span>
          </div>

          <div className="space-y-3.5">
            {reporte3Data?.rendimiento_veterinarios.map((vet, idx) => (
              <div key={idx} className="p-3 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-neutral-900">{vet.veterinario_nombre}</span>
                    <span className="text-[10px] text-neutral-500 ml-2 font-mono">({vet.matricula}) · {vet.especialidad}</span>
                  </div>
                  <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                    vet.tasa_derivacion_porcentaje >= 60 
                      ? 'bg-teal-100 text-teal-800 border border-teal-200' 
                      : vet.tasa_derivacion_porcentaje >= 30 
                      ? 'bg-amber-100 text-amber-800 border border-amber-200' 
                      : 'bg-blue-100 text-blue-800 border border-blue-200'
                  }`}>
                    {vet.perfil_prescriptivo}
                  </span>
                </div>

                <div className="w-full bg-neutral-200 h-2 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[#2D5864] rounded-full transition-all duration-500" 
                    style={{ width: `${Math.min(vet.tasa_derivacion_porcentaje, 100)}%` }}
                  />
                </div>

                <div className="flex flex-wrap items-center justify-between text-[11px] text-neutral-600 pt-0.5">
                  <span>
                    Atendidas: <strong className="text-neutral-800">{vet.turnos_atendidos}</strong> / {vet.turnos_asignados} ({vet.tasa_asistencia_porcentaje}% asis.)
                  </span>
                  <span>
                    Derivó: <strong className="text-teal-700">{vet.consultas_con_derivacion}</strong> ({vet.tasa_derivacion_porcentaje}%)
                  </span>
                  <span className="text-neutral-500 italic">
                    Más pedido: <strong className="text-neutral-700">{vet.estudio_frecuente}</strong>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-neutral-100 mb-4">
              <div className="flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-[#2D5864]" />
                <h4 className="font-bold text-sm text-[#2D5864]">
                  Top Estudios Prescriptos a Laboratorio
                </h4>
              </div>
              <span className="text-[10px] text-neutral-400">Total: {kpis?.total_estudios_solicitados} determinaciones</span>
            </div>

            <div className="space-y-3 mb-6">
              {reporte3Data?.top_estudios_prescriptos.slice(0, 5).map((est, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-neutral-700">{est.tipo_analisis}</span>
                    <span className="font-bold text-neutral-900">{est.cantidad} ({est.porcentaje}%)</span>
                  </div>
                  <div className="w-full bg-neutral-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-[#5F8E9C] rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(est.porcentaje * 2, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-neutral-100">
            <h5 className="text-[11px] font-bold text-neutral-600 mb-2 uppercase tracking-wider">
              Desglose de Estados de Agenda
            </h5>
            <div className="grid grid-cols-3 gap-2 text-center">
              {reporte3Data?.distribucion_estados_turno.map((item, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-[#FAF8F5] border border-[#F2E8D8]">
                  <div className="text-[11px] font-semibold text-neutral-600">{item.estado}</div>
                  <div className="text-sm font-extrabold text-[#2D5864] mt-0.5">{item.cantidad}</div>
                  <div className="text-[10px] text-neutral-400">{item.porcentaje}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white border border-[#E7E2DA] rounded-xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-[#E7E2DA] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[#FAF8F5]">
          <div>
            <h4 className="font-bold text-sm text-[#2D5864]">Registro de Consultas y Derivaciones Clínicas</h4>
            <p className="text-xs text-neutral-500">Trazabilidad de cada cita, diagnóstico presuntivo y prescripción de estudios</p>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              placeholder="Buscar paciente, médico, diagnóstico..."
              value={busquedaTabla}
              onChange={(e) => setBusquedaTabla(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 rounded-lg border border-[#E7E2DA] focus:outline-hidden focus:ring-1 focus:ring-[#2D5864] bg-white text-neutral-900"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-neutral-50 border-b border-neutral-200 text-neutral-600 font-semibold">
                <th className="py-2.5 px-3">Cita ID</th>
                <th className="py-2.5 px-3">Fecha / Hora</th>
                <th className="py-2.5 px-3">Paciente / Especie</th>
                <th className="py-2.5 px-3">Tutor</th>
                <th className="py-2.5 px-3">Médico Veterinario</th>
                <th className="py-2.5 px-3">Estado</th>
                <th className="py-2.5 px-3">Diagnóstico / Motivo</th>
                <th className="py-2.5 px-3 text-center">Derivación</th>
                <th className="py-2.5 px-3">Estudios Solicitados</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {cargando3 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-neutral-400">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-[#2D5864]" />
                    Cargando consultas clínicas...
                  </td>
                </tr>
              ) : consultasFiltradas.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-neutral-400">
                    No se encontraron registros que coincidan con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                consultasFiltradas.map((d, idx) => (
                  <tr key={idx} className="hover:bg-neutral-50/70 transition-colors">
                    <td className="py-2 px-3 font-mono font-medium text-neutral-700">{d.turno_id}</td>
                    <td className="py-2 px-3 text-neutral-600 whitespace-nowrap">{d.fecha_hora}</td>
                    <td className="py-2 px-3">
                      <div className="font-bold text-neutral-900">{d.paciente_nombre}</div>
                      <div className="text-[10px] text-neutral-500">{d.especie}</div>
                    </td>
                    <td className="py-2 px-3 text-neutral-700">{d.tutor_nombre}</td>
                    <td className="py-2 px-3">
                      <div className="font-semibold text-neutral-800">{d.veterinario_nombre}</div>
                      <div className="text-[10px] text-neutral-500">{d.especialidad}</div>
                    </td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        d.estado_turno === 'Atendido'
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          : d.estado_turno === 'Ausente'
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : 'bg-neutral-100 text-neutral-700 border border-neutral-200'
                      }`}>
                        {d.estado_turno}
                      </span>
                    </td>
                    <td className="py-2 px-3 max-w-[220px]">
                      <div className="font-medium text-neutral-800 truncate" title={d.diagnostico}>
                        {d.diagnostico}
                      </div>
                      <div className="text-[10px] text-neutral-500 truncate" title={d.motivo_consulta}>
                        {d.motivo_consulta}
                      </div>
                    </td>
                    <td className="py-2 px-3 text-center">
                      {d.derivo_laboratorio ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          {d.orden_numero}
                        </span>
                      ) : (
                        <span className="text-[10px] text-neutral-400">Sin orden</span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-neutral-600 max-w-[200px] truncate" title={d.estudios_solicitados}>
                      {d.estudios_solicitados}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {modalEmailOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#E7E2DA] rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-4 border-b border-[#E7E2DA] flex items-center justify-between bg-[#FAF8F5]">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-[#2D5864]" />
                <h4 className="font-bold text-sm text-[#2D5864]">
                  Enviar Reporte por Correo Electrónico
                </h4>
              </div>
              <button
                onClick={() => setModalEmailOpen(false)}
                className="text-neutral-400 hover:text-neutral-700 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={enviarEmail} className="p-5 space-y-4 text-xs">
              <div>
                <label className="block text-neutral-700 font-semibold mb-1">
                  Correo Electrónico Destinatario *
                </label>
                <input
                  type="email"
                  required
                  placeholder="ejemplo@veterinaria.com"
                  value={emailDestinatario}
                  onChange={e => setEmailDestinatario(e.target.value)}
                  className="w-full p-2.5 border border-[#E7E2DA] rounded-lg text-neutral-900 focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
                />
                <span className="text-[10px] text-neutral-400 mt-1 block">
                  Se enviará mediante el servidor SMTP oficial configurado en el sistema.
                </span>
              </div>

              <div>
                <label className="block text-neutral-700 font-semibold mb-1">
                  Asunto del Correo (Opcional)
                </label>
                <input
                  type="text"
                  placeholder="Auditoría Médica: Rendimiento Clínico y Derivación — Patitas & Co."
                  value={asuntoEmail}
                  onChange={e => setAsuntoEmail(e.target.value)}
                  className="w-full p-2.5 border border-[#E7E2DA] rounded-lg text-neutral-900 focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
                />
              </div>

              <div className="bg-[#FAF8F5] p-3 rounded-lg border border-[#F2E8D8] space-y-2">
                <span className="font-semibold text-neutral-800 block text-[11px]">Archivos adjuntos a incluir:</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={adjuntarPdf}
                    onChange={e => setAdjuntarPdf(e.target.checked)}
                    className="w-4 h-4 rounded text-[#2D5864] border-neutral-300 focus:ring-[#2D5864]"
                  />
                  <span className="text-neutral-700 font-medium">Acta Médica Oficial en PDF (.pdf)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={adjuntarExcel}
                    onChange={e => setAdjuntarExcel(e.target.checked)}
                    className="w-4 h-4 rounded text-[#2D5864] border-neutral-300 focus:ring-[#2D5864]"
                  />
                  <span className="text-neutral-700 font-medium">Libro de Consultas y Prescripciones en Excel (.xlsx)</span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-neutral-100">
                <button
                  type="button"
                  onClick={() => setModalEmailOpen(false)}
                  disabled={enviandoEmail}
                  className="px-3.5 py-2 text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={enviandoEmail || !emailDestinatario}
                  className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-xs"
                >
                  {enviandoEmail ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Enviando...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Enviar Informe</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};