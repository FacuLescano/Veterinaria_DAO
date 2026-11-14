import React, { useState, useEffect, useMemo } from 'react';
import { 
  Filter, 
  Search, 
  Microscope,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Layers,
  HeartPulse,
  PawPrint,
  Clock,
  Loader2
} from 'lucide-react';
import { useVeterinaria } from '../../../context/VeterinariaContext';
import { ReporteEficaciaResponse } from './types';
import { ReporteHeaderBanner, KpiCard, ReporteAccionesBar, ModalEnvioCorreo } from './common';

export const ReporteEficaciaDiagnostica: React.FC = () => {
  const { showToast } = useVeterinaria();

  const [reporte4Data, setReporte4Data] = useState<ReporteEficaciaResponse | null>(null);
  const [cargando4, setCargando4] = useState(false);

  // Filtros
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [filtroEspecie, setFiltroEspecie] = useState('Todas');
  const [filtroGrupoEtario, setFiltroGrupoEtario] = useState('Todos');
  const [filtroEstadoDiag, setFiltroEstadoDiag] = useState('Todos');
  const [filtroTipoAnalisis, setFiltroTipoAnalisis] = useState('Todos');
  const [busquedaTabla, setBusquedaTabla] = useState('');

  // Modal Enviar por Correo
  const [modalEmailOpen, setModalEmailOpen] = useState(false);
  const [enviandoEmail, setEnviandoEmail] = useState(false);

  const cargarReporte4 = async () => {
    setCargando4(true);
    try {
      const params = new URLSearchParams();
      if (fechaDesde) params.append('fecha_desde', fechaDesde);
      if (fechaHasta) params.append('fecha_hasta', fechaHasta);
      if (filtroEspecie !== 'Todas') params.append('especie', filtroEspecie);
      if (filtroGrupoEtario !== 'Todos') params.append('grupo_etario', filtroGrupoEtario);
      if (filtroEstadoDiag !== 'Todos') params.append('estado_diagnostico', filtroEstadoDiag);
      if (filtroTipoAnalisis !== 'Todos') params.append('tipo_analisis', filtroTipoAnalisis);

      const res = await fetch(`/api/v1/reportes/eficacia-diagnostica?${params.toString()}`);
      if (!res.ok) throw new Error('No se pudo obtener el reporte de eficacia diagnóstica');
      const data: ReporteEficaciaResponse = await res.json();
      setReporte4Data(data);
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Error al cargar reporte 4',
        description: err instanceof Error ? err.message : 'Error de comunicación con el backend.',
      });
    } finally {
      setCargando4(false);
    }
  };

  useEffect(() => {
    void cargarReporte4();
  }, [fechaDesde, fechaHasta, filtroEspecie, filtroGrupoEtario, filtroEstadoDiag, filtroTipoAnalisis]);

  const descargarArchivo = async (formato: 'excel' | 'pdf') => {
    try {
      const params = new URLSearchParams();
      if (fechaDesde) params.append('fecha_desde', fechaDesde);
      if (fechaHasta) params.append('fecha_hasta', fechaHasta);
      if (filtroEspecie !== 'Todas') params.append('especie', filtroEspecie);
      if (filtroGrupoEtario !== 'Todos') params.append('grupo_etario', filtroGrupoEtario);
      if (filtroEstadoDiag !== 'Todos') params.append('estado_diagnostico', filtroEstadoDiag);
      if (filtroTipoAnalisis !== 'Todos') params.append('tipo_analisis', filtroTipoAnalisis);

      const endpoint = `/api/v1/reportes/eficacia-diagnostica/${formato}?${params.toString()}`;
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`Error ${res.status}: Falló la descarga del archivo`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reporte_eficacia_diagnostica_${new Date().toISOString().slice(0, 10)}.${formato === 'excel' ? 'xlsx' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast({
        type: 'success',
        title: `Descarga de ${formato.toUpperCase()} completada`,
        description: 'El archivo oficial se generó exitosamente.',
      });
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Fallo de descarga',
        description: err instanceof Error ? err.message : 'No se pudo descargar el reporte.',
      });
    }
  };

  const handleEnviarEmail = async (
    destinatario: string,
    asunto: string,
    adjuntarPdf: boolean,
    adjuntarExcel: boolean
  ) => {
    setEnviandoEmail(true);
    try {
      const payload = {
        destinatario,
        asunto: asunto || undefined,
        incluir_pdf: adjuntarPdf,
        incluir_excel: adjuntarExcel,
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
        especie: filtroEspecie !== 'Todas' ? filtroEspecie : undefined,
        grupo_etario: filtroGrupoEtario !== 'Todos' ? filtroGrupoEtario : undefined,
        estado_diagnostico: filtroEstadoDiag !== 'Todos' ? filtroEstadoDiag : undefined,
        tipo_analisis: filtroTipoAnalisis !== 'Todos' ? filtroTipoAnalisis : undefined,
      };

      const res = await fetch('/api/v1/reportes/eficacia-diagnostica/enviar-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.mensaje || 'Error al enviar correo');

      showToast({
        type: 'success',
        title: 'Reporte enviado con éxito',
        description: `Se remitió el acta de eficacia diagnóstica a ${destinatario}`,
      });
      setModalEmailOpen(false);
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Error de envío de correo',
        description: err instanceof Error ? err.message : 'No se pudo contactar con el servidor SMTP.',
      });
    } finally {
      setEnviandoEmail(false);
    }
  };

  // Filtrado reactivo en memoria para el buscador de la tabla
  const detallesFiltrados = useMemo(() => {
    if (!reporte4Data) return [];
    if (!busquedaTabla.trim()) return reporte4Data.detalles_diagnosticos;

    const q = busquedaTabla.toLowerCase();
    return reporte4Data.detalles_diagnosticos.filter(d =>
      d.paciente_nombre.toLowerCase().includes(q) ||
      d.tutor_nombre.toLowerCase().includes(q) ||
      d.especie.toLowerCase().includes(q) ||
      d.tipo_analisis.toLowerCase().includes(q) ||
      d.diagnostico_presuntivo.toLowerCase().includes(q) ||
      d.parametros_resumen.toLowerCase().includes(q) ||
      d.veterinario_nombre.toLowerCase().includes(q)
    );
  }, [reporte4Data, busquedaTabla]);

  return (
    <div className="space-y-6">
      {/* Banner Superior Reutilizable (Limpio, sin badges) */}
      <ReporteHeaderBanner
        titulo="PATITAS & CO. — EFICACIA DIAGNÓSTICA Y HALLAZGOS CRÍTICOS"
        subtitulo="Reporte 4: Positividad Analítica, Concordancia Presuntiva y Epidemiología Veterinaria"
      />

      {/* Barra de Filtros y Acciones */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#2D5864]" />
            <span className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Filtros Epidemiológicos:</span>
          </div>

          <ReporteAccionesBar
            onDescargarExcel={() => void descargarArchivo('excel')}
            onDescargarPdf={() => void descargarArchivo('pdf')}
            onAbrirModalEmail={() => setModalEmailOpen(true)}
            onRecargar={() => void cargarReporte4()}
            cargando={cargando4}
          />
        </div>

        {/* Inputs de filtros en grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-2 border-t border-neutral-100 text-xs">
          {/* Especie */}
          <div>
            <label className="block text-neutral-500 font-semibold mb-1">Especie:</label>
            <select
              value={filtroEspecie}
              onChange={e => setFiltroEspecie(e.target.value)}
              className="w-full p-2 border border-[#E7E2DA] rounded-lg text-neutral-800 bg-white focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
            >
              {reporte4Data?.filtros_disponibles.especies.map(esp => (
                <option key={esp} value={esp}>{esp}</option>
              )) || <option value="Todas">Todas</option>}
            </select>
          </div>

          {/* Grupo Etario */}
          <div>
            <label className="block text-neutral-500 font-semibold mb-1">Grupo Etario:</label>
            <select
              value={filtroGrupoEtario}
              onChange={e => setFiltroGrupoEtario(e.target.value)}
              className="w-full p-2 border border-[#E7E2DA] rounded-lg text-neutral-800 bg-white focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
            >
              {reporte4Data?.filtros_disponibles.grupos_etarios.map(grp => (
                <option key={grp} value={grp}>{grp}</option>
              )) || <option value="Todos">Todos</option>}
            </select>
          </div>

          {/* Estado Diagnóstico */}
          <div>
            <label className="block text-neutral-500 font-semibold mb-1">Estado Diagnóstico:</label>
            <select
              value={filtroEstadoDiag}
              onChange={e => setFiltroEstadoDiag(e.target.value)}
              className="w-full p-2 border border-[#E7E2DA] rounded-lg text-neutral-800 bg-white focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
            >
              {reporte4Data?.filtros_disponibles.estados_diagnosticos.map(est => (
                <option key={est} value={est}>{est}</option>
              )) || <option value="Todos">Todos</option>}
            </select>
          </div>

          {/* Tipo de Análisis */}
          <div>
            <label className="block text-neutral-500 font-semibold mb-1">Tipo de Análisis:</label>
            <select
              value={filtroTipoAnalisis}
              onChange={e => setFiltroTipoAnalisis(e.target.value)}
              className="w-full p-2 border border-[#E7E2DA] rounded-lg text-neutral-800 bg-white focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
            >
              {reporte4Data?.filtros_disponibles.tipos_analisis.map(tipo => (
                <option key={tipo} value={tipo}>{tipo}</option>
              )) || <option value="Todos">Todos</option>}
            </select>
          </div>

          {/* Fecha Desde */}
          <div>
            <label className="block text-neutral-500 font-semibold mb-1">Desde:</label>
            <input
              type="date"
              value={fechaDesde}
              onChange={e => setFechaDesde(e.target.value)}
              className="w-full p-1.5 border border-[#E7E2DA] rounded-lg text-neutral-800 bg-white focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
            />
          </div>

          {/* Fecha Hasta */}
          <div>
            <label className="block text-neutral-500 font-semibold mb-1">Hasta:</label>
            <input
              type="date"
              value={fechaHasta}
              onChange={e => setFechaHasta(e.target.value)}
              className="w-full p-1.5 border border-[#E7E2DA] rounded-lg text-neutral-800 bg-white focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
            />
          </div>
        </div>
      </div>

      {/* Tarjetas KPIs Reutilizables */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard
          titulo="Estudios Procesados"
          valor={reporte4Data?.kpis.total_estudios_procesados ?? '-'}
          subtexto="Determinaciones analíticas"
          icono={Microscope}
          colorIcono="text-blue-600"
          colorValor="text-[#2D5864]"
        />
        <KpiCard
          titulo="Hallazgos Patológicos"
          valor={reporte4Data?.kpis.total_con_hallazgos_criticos ?? '-'}
          subtexto="Con analitos fuera de rango"
          icono={AlertTriangle}
          colorIcono="text-red-500"
          colorValor="text-red-600"
        />
        <KpiCard
          titulo="Tasa de Positividad"
          valor={reporte4Data ? `${reporte4Data.kpis.tasa_positividad_porcentaje}%` : '-'}
          subtexto="Índice de detección patológica"
          icono={Activity}
          colorIcono="text-amber-500"
          colorValor="text-amber-700"
        />
        <KpiCard
          titulo="Concordancia Médica"
          valor={reporte4Data ? `${reporte4Data.kpis.tasa_concordancia_diagnostica}%` : '-'}
          subtexto="Confirmación presuntiva"
          icono={CheckCircle2}
          colorIcono="text-emerald-500"
          colorValor="text-emerald-700"
        />
        <KpiCard
          titulo="Fisiológicos Normales"
          valor={reporte4Data?.kpis.total_fisiologicos_normales ?? '-'}
          subtexto="Dentro de rango estándar"
          icono={HeartPulse}
          colorIcono="text-emerald-500"
          colorValor="text-emerald-700"
        />
        <KpiCard
          titulo="Especies Auditadas"
          valor={reporte4Data?.kpis.total_especies_auditadas ?? '-'}
          subtexto="Población multiespecie auditada"
          icono={PawPrint}
          colorIcono="text-blue-600"
          colorValor="text-blue-800"
        />
      </div>

      {/* Gráficos / Paneles Analíticos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Panel 1: Positividad por Especie y Grupo Etario */}
        <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <PawPrint className="w-4 h-4 text-[#2D5864]" />
              <h4 className="font-bold text-xs text-neutral-800 uppercase tracking-wider">
                Distribución Epidemiológica por Especie
              </h4>
            </div>
            <span className="text-[10px] text-neutral-400 font-mono">Auditoría Poblacional</span>
          </div>

          <div className="space-y-4">
            {reporte4Data?.desglose_por_especie.map(esp => (
              <div key={esp.especie} className="p-3 bg-neutral-50 rounded-lg border border-neutral-100 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-neutral-900">{esp.especie}</span>
                  <span className="text-[11px] font-semibold text-[#2D5864]">
                    {esp.patologicos} patológicos / {esp.total_estudios} estudios ({esp.tasa_positividad_porcentaje}%)
                  </span>
                </div>
                {/* Barra de progreso */}
                <div className="w-full bg-neutral-200 h-2 rounded-full overflow-hidden flex">
                  <div
                    className="bg-red-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${esp.tasa_positividad_porcentaje}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[10px] text-neutral-500 pt-1">
                  <span>Predominio: <strong className="text-neutral-700">{esp.patologia_predominante}</strong></span>
                  <span className="text-emerald-700 font-medium">{esp.normales} normales ({100 - esp.tasa_positividad_porcentaje}%)</span>
                </div>
              </div>
            )) || (
              <p className="text-xs text-neutral-400 text-center py-4">Cargando distribución de especies...</p>
            )}
          </div>

          {/* Subpanel: Grupo Etario */}
          <div className="pt-2 border-t border-neutral-100">
            <span className="text-[11px] font-bold text-neutral-700 block mb-2">Positividad por Grupo Etario:</span>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              {reporte4Data?.desglose_por_grupo_etario.map(grp => (
                <div key={grp.grupo_etario} className="p-2 bg-[#FAF8F5] border border-[#F2E8D8] rounded-lg">
                  <span className="text-[10px] text-neutral-500 font-medium block truncate">{grp.grupo_etario}</span>
                  <span className="text-sm font-bold text-[#2D5864] block mt-0.5">{grp.tasa_positividad_porcentaje}%</span>
                  <span className="text-[9px] text-neutral-400 block">{grp.patologicos}/{grp.total_estudios} casos</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Panel 2: Top de Analitos Críticos Fuera de Rango */}
        <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#2D5864]" />
              <h4 className="font-bold text-xs text-neutral-800 uppercase tracking-wider">
                Top de Parámetros Críticos Fuera de Rango
              </h4>
            </div>
            <span className="text-[10px] text-neutral-400 font-mono">Frecuencia de Desviación</span>
          </div>

          <div className="space-y-3">
            {reporte4Data?.top_analitos_criticos.slice(0, 5).map(ana => (
              <div key={ana.parametro} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-neutral-800">{ana.parametro}</span>
                    <span className="text-[10px] text-neutral-400 font-normal">({ana.tipo_analisis})</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                      ana.tipo_alerta_predominante === 'Alto' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                    }`}>
                      {ana.tipo_alerta_predominante}
                    </span>
                    <span className="font-semibold text-neutral-700">{ana.frecuencia_alerta} alertas ({ana.porcentaje_incidencia}%)</span>
                  </div>
                </div>
                <div className="w-full bg-neutral-100 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-[#2D5864] h-full rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(ana.porcentaje_incidencia * 2.5, 100)}%` }}
                  />
                </div>
              </div>
            )) || (
              <p className="text-xs text-neutral-400 text-center py-4">Cargando top de parámetros...</p>
            )}
          </div>

          {/* Distribución de Severidad */}
          <div className="pt-3 border-t border-neutral-100">
            <span className="text-[11px] font-bold text-neutral-700 block mb-2">Desglose por Severidad Diagnóstica:</span>
            <div className="flex items-center gap-2">
              {reporte4Data?.distribucion_severidad.map(sev => (
                <div
                  key={sev.severidad}
                  className={`flex-1 p-2 rounded-lg text-center border ${
                    sev.severidad === 'Crítico'
                      ? 'bg-red-50 border-red-200 text-red-900'
                      : sev.severidad === 'Moderado'
                      ? 'bg-amber-50 border-amber-200 text-amber-900'
                      : 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  }`}
                >
                  <span className="text-[10px] font-semibold block">{sev.severidad}</span>
                  <span className="text-sm font-bold block">{sev.cantidad} ({sev.porcentaje}%)</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tabla Detallada de Auditoría Diagnóstica */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl shadow-xs overflow-hidden space-y-3 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#2D5864]" />
            <h4 className="font-bold text-xs text-neutral-900 uppercase tracking-wider">
              Auditoría Clínica de Resultados y Correlación Presuntiva
            </h4>
            <span className="text-xs text-neutral-400">({detallesFiltrados.length} registros)</span>
          </div>

          {/* Buscador reactivo */}
          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 text-neutral-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Buscar por paciente, tutor, analito..."
              value={busquedaTabla}
              onChange={e => setBusquedaTabla(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 border border-[#E7E2DA] rounded-lg text-xs text-neutral-900 focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
            />
          </div>
        </div>

        <div className="overflow-x-auto border border-neutral-100 rounded-lg">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#FAF8F5] text-neutral-600 font-semibold border-b border-[#F2E8D8]">
                <th className="p-3">Paciente / Tutor</th>
                <th className="p-3">Especie / Edad</th>
                <th className="p-3">Estudio / Fecha</th>
                <th className="p-3">Diagnóstico Presuntivo</th>
                <th className="p-3">Parámetros Alterados</th>
                <th className="p-3 text-center">Estado / Severidad</th>
                <th className="p-3">Conclusión de Laboratorio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {cargando4 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-neutral-400">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-[#2D5864]" />
                    <span>Cargando auditoría de eficacia diagnóstica...</span>
                  </td>
                </tr>
              ) : detallesFiltrados.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-neutral-400">
                    No se encontraron registros de eficacia para los filtros aplicados.
                  </td>
                </tr>
              ) : (
                detallesFiltrados.map((d, idx) => (
                  <tr key={`${d.resultado_id}-${idx}`} className="hover:bg-neutral-50/70 transition-colors">
                    {/* Paciente / Tutor */}
                    <td className="p-3">
                      <div className="font-bold text-neutral-900">{d.paciente_nombre}</div>
                      <div className="text-[10px] text-neutral-400">{d.tutor_nombre}</div>
                    </td>

                    {/* Especie / Edad */}
                    <td className="p-3">
                      <div className="font-semibold text-neutral-800">{d.especie} ({d.raza})</div>
                      <div className="text-[10px] text-neutral-500">{d.grupo_etario} · {d.edad_anios} años</div>
                    </td>

                    {/* Estudio / Fecha */}
                    <td className="p-3">
                      <div className="font-bold text-[#2D5864]">{d.tipo_analisis}</div>
                      <div className="text-[10px] text-neutral-400 flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3 text-neutral-400" />
                        <span>{d.fecha_emision}</span>
                      </div>
                    </td>

                    {/* Diagnóstico Presuntivo */}
                    <td className="p-3 max-w-xs">
                      <div className="font-medium text-neutral-800 line-clamp-2">{d.diagnostico_presuntivo}</div>
                      <div className="text-[10px] text-neutral-400">Médico: {d.veterinario_nombre}</div>
                    </td>

                    {/* Parámetros Alterados */}
                    <td className="p-3 max-w-xs">
                      {d.lista_parametros_alerta.length > 0 ? (
                        <div className="space-y-1">
                          {d.lista_parametros_alerta.map((p, pIdx) => (
                            <div key={pIdx} className="text-[11px] flex items-center gap-1.5">
                              <span className={`w-1.5 h-1.5 rounded-full ${p.alerta === 'Alto' ? 'bg-red-500' : 'bg-blue-500'}`} />
                              <span className="font-medium text-neutral-800">{p.parametro}:</span>
                              <span className="font-bold text-neutral-900">{p.valor} {p.unidad}</span>
                              <span className="text-[9px] text-neutral-400">({p.alerta})</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-[11px] text-emerald-700 font-medium">✓ Dentro de rango fisiológico</span>
                      )}
                    </td>

                    {/* Estado / Severidad */}
                    <td className="p-3 text-center">
                      <span className={`inline-block text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                        d.estado_diagnostico === 'Hallazgo Patológico'
                          ? 'bg-red-50 text-red-800 border-red-200'
                          : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      }`}>
                        {d.estado_diagnostico}
                      </span>
                      <span className="block text-[9px] text-neutral-400 mt-1 font-mono">
                        {d.severidad}
                      </span>
                    </td>

                    {/* Conclusión de Laboratorio */}
                    <td className="p-3 max-w-xs text-[11px] text-neutral-600 line-clamp-3">
                      {d.conclusion_laboratorio}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Reutilizable de Envio por Correo */}
      <ModalEnvioCorreo
        isOpen={modalEmailOpen}
        onClose={() => setModalEmailOpen(false)}
        onEnviar={handleEnviarEmail}
        enviando={enviandoEmail}
        tituloReporte="Reporte de Eficacia Diagnóstica"
        placeholderAsunto="Reporte de Eficacia Diagnóstica y Hallazgos Críticos — Patitas & Co."
        etiquetaPdf="Acta Oficial de Eficacia Diagnóstica en PDF (.pdf)"
        etiquetaExcel="Libro analítico epidemiológico en Excel (.xlsx)"
      />
    </div>
  );
};
