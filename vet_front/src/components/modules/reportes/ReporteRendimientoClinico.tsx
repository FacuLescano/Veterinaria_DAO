import React, { useState, useEffect, useMemo } from 'react';
import { 
  Filter, 
  Search, 
  Calendar,
  CalendarCheck,
  CalendarX,
  TrendingUp,
  FlaskConical,
  ClipboardList,
  Award,
  CheckCircle2,
  Loader2
} from 'lucide-react';
import { useVeterinaria } from '../../../context/VeterinariaContext';
import { ReporteRendimientoClinicoResponse } from './types';
import { ReporteHeaderBanner, KpiCard, ReporteAccionesBar, ModalEnvioCorreo } from './common';

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

  const enviarEmail = async (destinatario: string, asunto: string, incluirPdf: boolean, incluirExcel: boolean) => {
    setEnviandoEmail(true);
    try {
      const body = {
        destinatario,
        asunto: asunto || undefined,
        incluir_pdf: incluirPdf,
        incluir_excel: incluirExcel,
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
        description: data.mensaje || `El informe oficial fue enviado con éxito a ${destinatario}.`
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
      {/* Banner Superior Reutilizable */}
      <ReporteHeaderBanner
        titulo="PATITAS & CO. — RENDIMIENTO CLÍNICO Y TASA DE DERIVACIÓN MÉDICA"
        subtitulo="Reporte 3: Auditoría de Consultas, Ausentismo y Prescripción de Laboratorio"
      />

      {/* Barra de Filtros y Acciones */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#2D5864]" />
            <span className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Filtros Clínicos:</span>
          </div>

          <ReporteAccionesBar
            onDescargarExcel={() => void descargarArchivo('excel')}
            onDescargarPdf={() => void descargarArchivo('pdf')}
            onAbrirModalEmail={() => setModalEmailOpen(true)}
            onRecargar={() => void cargarReporte3()}
            cargando={cargando3}
          />
        </div>

        {/* Dropdowns de Filtrado */}
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

      {/* Tarjetas KPIs Reutilizables */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <KpiCard
            titulo="Agendados"
            valor={kpis.total_turnos_agendados}
            unidad="turnos"
            subtexto="100% de la agenda"
            icono={Calendar}
            colorIcono="text-[#2D5864]"
            colorValor="text-[#2D5864]"
          />
          <KpiCard
            titulo="Atendidos"
            valor={kpis.turnos_atendidos}
            unidad={`(${kpis.tasa_asistencia_porcentaje}%)`}
            subtexto="Efectividad de asistencia"
            icono={CalendarCheck}
            colorIcono="text-emerald-600"
            colorValor="text-emerald-700"
          />
          <KpiCard
            titulo="Ausentismo"
            valor={`${kpis.tasa_ausentismo_porcentaje}%`}
            unidad="no-show"
            subtexto={`${kpis.turnos_ausentes} ausencias registradas`}
            icono={CalendarX}
            colorIcono="text-rose-600"
            colorValor={kpis.tasa_ausentismo_porcentaje > 15 ? 'text-rose-700' : 'text-neutral-800'}
          />
          <KpiCard
            titulo="Derivación Lab"
            valor={`${kpis.tasa_derivacion_global_porcentaje}%`}
            unidad={`(${kpis.consultas_con_derivacion})`}
            subtexto={`De ${kpis.turnos_atendidos} consultas`}
            icono={TrendingUp}
            colorIcono="text-teal-600"
            colorValor="text-teal-700"
          />
          <KpiCard
            titulo="Órdenes Lab"
            valor={kpis.total_ordenes_laboratorio}
            unidad="pedidos"
            subtexto="Prescripciones a central"
            icono={FlaskConical}
            colorIcono="text-[#2D5864]"
            colorValor="text-[#2D5864]"
          />
          <KpiCard
            titulo="Determinaciones"
            valor={kpis.total_estudios_solicitados}
            unidad="análisis"
            subtexto={`Prom. ${kpis.promedio_estudios_por_orden} por orden`}
            icono={ClipboardList}
            colorIcono="text-indigo-600"
            colorValor="text-indigo-800"
          />
        </div>
      )}

      {/* Gráficos y Tablas Analíticas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Columna Izquierda: Desempeño y Tasa de Derivación por Médico Veterinario */}
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

        {/* Columna Derecha: Top Estudios Prescriptos & Desglose de Estado de Citas */}
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

      {/* Tabla de Detalle de Consultas y Auditoría Clínica */}
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

      {/* Modal Reutilizable */}
      <ModalEnvioCorreo
        isOpen={modalEmailOpen}
        onClose={() => setModalEmailOpen(false)}
        onEnviar={enviarEmail}
        enviando={enviandoEmail}
        tituloReporte="Auditoría Médica: Rendimiento Clínico y Derivación"
        placeholderAsunto="Auditoría Médica: Rendimiento Clínico y Derivación — Patitas & Co."
        etiquetaPdf="Acta Médica Oficial en PDF (.pdf)"
        etiquetaExcel="Libro de Consultas y Prescripciones en Excel (.xlsx)"
      />
    </div>
  );
};
