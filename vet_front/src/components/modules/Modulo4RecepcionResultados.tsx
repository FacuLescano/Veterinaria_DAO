import React, { useEffect, useState } from 'react';
import { useVeterinaria } from '../../context/VeterinariaContext';
import { RemitoBiologico, EstadoPrecinto, ResultadoAnalisis } from '../../types/veterinaria';
import { Modal } from '../common/Modal';
import { 
  ClipboardCheck, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  FileText, 
  Plus, 
  CheckCircle, 
  XCircle, 
  Upload, 
  FileCheck2,
  Calendar,
  AlertCircle
} from 'lucide-react';

export const Modulo4RecepcionResultados: React.FC = () => {
  const {
    remitos,
    muestras,
    ordenes,
    mascotas,
    incidencias,
    resultados,
    verificarPrecintoYRecepcion,
    registrarResultado,
    resolverIncidencia,
    showToast
  } = useVeterinaria();

  const [activeTab, setActiveTab] = useState<'recepcion' | 'resultados' | 'incidencias'>('recepcion');

  // Modals
  const [isVerificarModalOpen, setIsVerificarModalOpen] = useState(false);
  const [selectedRemito, setSelectedRemito] = useState<RemitoBiologico | null>(null);

  const [isCargarResultadoModalOpen, setIsCargarResultadoModalOpen] = useState(false);
  const [selectedIncidenciaForResolve, setSelectedIncidenciaForResolve] = useState<string | null>(null);
  const [resolucionTexto, setResolucionTexto] = useState('');

  // Form State for Verification
  const [verificacionData, setVerificacionData] = useState({
    estadoPrecinto: 'Integro' as EstadoPrecinto,
    verificadoPor: 'Bioq. Gabriela Torres (Lab Central BioVet)',
    observaciones: 'Precinto inspeccionado visualmente al abrir conservadora.'
  });

  // Form State for Lab Results
  const [resultadoData, setResultadoData] = useState({
    ordenId: ordenes[0]?.id || '',
    detalleAnalisisId: ordenes[0]?.detalles[0]?.id || '',
    muestraId: muestras[0]?.id || '',
    laboratorioNombre: 'Laboratorio Central de Derivaciones BioVet',
    param1: { parametro: 'Glóbulos Rojos (RBC)', valor: '6.4', unidad: 'M/uL', rango: '5.5 - 8.5', alerta: 'Normal' as any },
    param2: { parametro: 'Glóbulos Blancos (WBC)', valor: '18.9', unidad: 'K/uL', rango: '6.0 - 17.0', alerta: 'Alto' as any },
    param3: { parametro: 'ALT / GPT (Transaminasa)', valor: '112', unidad: 'U/L', rango: '10 - 100', alerta: 'Alto' as any },
    conclusionDiagnostica: 'Leve leucocitosis reactiva y elevación moderada de transaminasas compatible con inflamación hepática aguda.',
    nombreArchivoAdjunto: 'Informe_BioVet_ORD-2026.pdf',
    estado: 'Validado por Veterinario' as any,
    validadoPor: 'Dr. Alejandro Morales'
  });

  useEffect(() => {
    const orden = ordenes[0];
    const muestra = muestras.find((m) => m.estadoActual === 'Recibida') || muestras[0];
    if (orden && (!ordenes.some((o) => o.id === resultadoData.ordenId))) setResultadoData((d) => ({ ...d, ordenId: orden.id, detalleAnalisisId: orden.detalles[0]?.id || '' }));
    if (muestra && !muestras.some((m) => m.id === resultadoData.muestraId)) setResultadoData((d) => ({ ...d, muestraId: muestra.id }));
  }, [ordenes, muestras, resultadoData.ordenId, resultadoData.muestraId]);

  // Pending shipments
  const enviosPendientes = remitos.filter(r => r.estado === 'Despachado');

  const openVerificarModal = (r: RemitoBiologico) => {
    setSelectedRemito(r);
    setVerificacionData({
      estadoPrecinto: 'Integro',
      verificadoPor: 'Bioq. Gabriela Torres (Lab Central BioVet)',
      observaciones: `Precinto ${r.precintoCodigo} contrastado con remito ${r.id}.`
    });
    setIsVerificarModalOpen(true);
  };

  const handleConfirmarRecepcion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRemito) return;

    try {
    await verificarPrecintoYRecepcion({
      remitoId: selectedRemito.id,
      estadoPrecinto: verificacionData.estadoPrecinto,
      verificadoPor: verificacionData.verificadoPor,
      observaciones: verificacionData.observaciones
    });

    setIsVerificarModalOpen(false);
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo registrar la recepción', description: error instanceof Error ? error.message : 'Verificá la conexión y el envío.' });
    }
  };

  const handleGuardarResultado = async (e: React.FormEvent) => {
    e.preventDefault();
    const now = new Date().toISOString().replace('T', ' ').substring(0, 16);

    try {
    await registrarResultado({
      ordenId: resultadoData.ordenId,
      detalleAnalisisId: resultadoData.detalleAnalisisId,
      muestraId: resultadoData.muestraId,
      fechaRecepcionResultado: now,
      laboratorioNombre: resultadoData.laboratorioNombre,
      valores: [
        {
          parametro: resultadoData.param1.parametro,
          valor: resultadoData.param1.valor,
          unidad: resultadoData.param1.unidad,
          rangoReferencia: resultadoData.param1.rango,
          alerta: resultadoData.param1.alerta
        },
        {
          parametro: resultadoData.param2.parametro,
          valor: resultadoData.param2.valor,
          unidad: resultadoData.param2.unidad,
          rangoReferencia: resultadoData.param2.rango,
          alerta: resultadoData.param2.alerta
        },
        {
          parametro: resultadoData.param3.parametro,
          valor: resultadoData.param3.valor,
          unidad: resultadoData.param3.unidad,
          rangoReferencia: resultadoData.param3.rango,
          alerta: resultadoData.param3.alerta
        }
      ],
      conclusionDiagnostica: resultadoData.conclusionDiagnostica,
      nombreArchivoAdjunto: resultadoData.nombreArchivoAdjunto,
      estado: resultadoData.estado,
      validadoPor: resultadoData.validadoPor
    });

    setIsCargarResultadoModalOpen(false);
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo guardar el resultado', description: error instanceof Error ? error.message : 'Verificá la orden, el análisis y la muestra.' });
    }
  };

  const handleResolveIncidencia = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncidenciaForResolve || !resolucionTexto) return;

    try {
      await resolverIncidencia(selectedIncidenciaForResolve, resolucionTexto);
      setSelectedIncidenciaForResolve(null);
      setResolucionTexto('');
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo resolver la incidencia', description: error instanceof Error ? error.message : 'Verificá el estado de la incidencia.' });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Segmented Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E7E2DA] pb-4">
        <div className="inline-flex items-center p-1 bg-[#FAF6EF] border border-[#E7E2DA] rounded-xl">
          <button
            onClick={() => setActiveTab('recepcion')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'recepcion'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Recepción & Verificación de Precinto ({enviosPendientes.length})
          </button>
          <button
            onClick={() => setActiveTab('resultados')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'resultados'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Resultados de Laboratorio ({resultados.length})
          </button>
          <button
            onClick={() => setActiveTab('incidencias')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'incidencias'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Incidencias y Anomalías ({incidencias.length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'resultados' && (
            <button
              onClick={() => setIsCargarResultadoModalOpen(true)}
              className="px-3 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Cargar Resultado Externo</span>
            </button>
          )}
        </div>
      </div>

      {/* TAB 1: RECEPCIÓN Y VERIFICACIÓN DE PRECINTO */}
      {activeTab === 'recepcion' && (
        <div className="space-y-4">
          <div className="bg-white border border-[#E7E2DA] rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 border-b border-[#F2E8D8] flex items-center justify-between bg-[#FAF8F5]">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#2D5864]">
                  Envíos Despachados Pendientes de Recepción
                </h4>
                <p className="text-[11px] text-neutral-500">
                  Verifique el código y estado del precinto sanitario para garantizar la viabilidad biológica
                </p>
              </div>
              <span className="text-xs font-mono text-neutral-600 bg-white px-2 py-1 rounded border border-neutral-200">
                {enviosPendientes.length} en tránsito
              </span>
            </div>

            {enviosPendientes.length === 0 ? (
              <div className="p-8 text-center text-neutral-400 text-xs">
                No hay envíos en tránsito actualmente. Todos los remitos han sido recibidos o procesados.
              </div>
            ) : (
              <div className="divide-y divide-neutral-100">
                {enviosPendientes.map(r => {
                  return (
                    <div
                      key={r.id}
                      className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-neutral-50/50 transition-colors"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-[#2D5864]">{r.id}</span>
                          <span className="text-neutral-300">·</span>
                          <span className="text-xs font-medium text-neutral-700">
                            {r.clinicaOrigen} → {r.laboratorioDestino}
                          </span>
                        </div>
                        <div className="text-xs text-neutral-600 flex flex-wrap items-center gap-3">
                          <span>
                            Contenedor: <strong className="font-mono text-neutral-900">{r.conservadoraId}</strong>
                          </span>
                          <span aria-hidden="true" className="text-neutral-300">·</span>
                          <span className="flex items-center gap-1 text-[#2D5864] font-medium">
                            <ShieldCheck className="w-3.5 h-3.5" />
                            Precinto: <strong className="font-mono">{r.precintoCodigo}</strong>
                          </span>
                          <span aria-hidden="true" className="text-neutral-300">·</span>
                          <span>
                            Muestras: <strong className="font-mono">{r.muestrasIds.length}</strong> ({r.muestrasIds.join(', ')})
                          </span>
                          <span aria-hidden="true" className="text-neutral-300">·</span>
                          <span>Transportista: {r.transportista}</span>
                        </div>
                      </div>

                      <div className="shrink-0">
                        <button
                          onClick={() => openVerificarModal(r)}
                          className="px-3.5 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-2 shadow-xs"
                        >
                          <ShieldCheck className="w-4 h-4" />
                          <span>Verificar Precinto & Recibir</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Quick Notice about University Business Rule */}
          <div className="p-4 bg-[#FAF8F5] rounded-xl border border-[#F2E8D8] text-xs space-y-1.5 text-neutral-700">
            <div className="flex items-center gap-2 font-bold text-[#2D5864]">
              <ShieldAlert className="w-4 h-4" />
              <span>Regla de Validación de Negocio (Cátedra):</span>
            </div>
            <p className="text-[11px] leading-relaxed text-neutral-600">
              Si el precinto sanitario se encuentra <strong>roto, violado o el código no coincide</strong>, el sistema impide automáticamente el procesamiento de las muestras y transiciona su estado de manera inmutable a <strong>Muestra Rechazada</strong>, registrando la incidencia respectiva sin alterar los estados históricos previos.
            </p>
          </div>
        </div>
      )}

      {/* TAB 2: RESULTADOS DE LABORATORIO */}
      {activeTab === 'resultados' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {resultados.map(res => {
              const pet = mascotas.find(m => m.id === 'MASC-001'); // fallback / match
              const ord = ordenes.find(o => o.id === res.ordenId);

              return (
                <div key={res.id} className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-neutral-100 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-[#2D5864]">{res.id}</span>
                        <span className="text-neutral-300">·</span>
                        <h4 className="font-bold text-sm text-neutral-900">
                          Informe de {res.laboratorioNombre}
                        </h4>
                        <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          {res.estado}
                        </span>
                      </div>
                      <p className="text-xs text-neutral-500 mt-0.5">
                        Orden: <strong className="font-mono text-neutral-800">{res.ordenId}</strong> · Muestra:{' '}
                        <strong className="font-mono text-neutral-800">{res.muestraId}</strong> · Recibido: {res.fechaRecepcionResultado}
                      </p>
                    </div>

                    {res.validadoPor && (
                      <span className="text-xs text-neutral-600">
                        Validado por: <strong>{res.validadoPor}</strong>
                      </span>
                    )}
                  </div>

                  {/* Param values table */}
                  <div className="overflow-x-auto border border-neutral-200 rounded-lg">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-neutral-50 text-neutral-600 border-b border-neutral-200">
                        <tr>
                          <th className="py-2 px-3 font-semibold">Parámetro / Determinación</th>
                          <th className="py-2 px-3 font-semibold">Valor Hallado</th>
                          <th className="py-2 px-3 font-semibold">Unidad</th>
                          <th className="py-2 px-3 font-semibold">Rango de Referencia</th>
                          <th className="py-2 px-3 font-semibold">Interpretación</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-100">
                        {res.valores.map((v, i) => (
                          <tr key={i} className="hover:bg-neutral-50/50">
                            <td className="py-2 px-3 font-medium text-neutral-800">{v.parametro}</td>
                            <td className="py-2 px-3 font-mono font-bold text-neutral-900">{v.valor}</td>
                            <td className="py-2 px-3 text-neutral-500 font-mono">{v.unidad}</td>
                            <td className="py-2 px-3 text-neutral-600 font-mono">{v.rangoReferencia}</td>
                            <td className="py-2 px-3">
                              <span
                                className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                                  v.alerta === 'Alto'
                                    ? 'bg-amber-100 text-amber-800'
                                    : v.alerta === 'Bajo'
                                    ? 'bg-rose-100 text-rose-800'
                                    : 'bg-emerald-100 text-emerald-800'
                                }`}
                              >
                                {v.alerta || 'Normal'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Conclusion */}
                  <div className="p-3 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] text-xs">
                    <span className="font-semibold text-neutral-800 block mb-0.5">
                      Conclusión Diagnóstica del Laboratorio:
                    </span>
                    <p className="text-neutral-700 leading-relaxed">{res.conclusionDiagnostica}</p>
                    {res.nombreArchivoAdjunto && (
                      <div className="mt-2 text-[11px] text-[#2D5864] flex items-center gap-1.5 font-mono">
                        <FileText className="w-3.5 h-3.5" />
                        <span>Archivo adjunto: {res.nombreArchivoAdjunto}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 3: INCIDENCIAS */}
      {activeTab === 'incidencias' && (
        <div className="space-y-4">
          <div className="bg-white border border-[#E7E2DA] rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 border-b border-[#F2E8D8] flex items-center justify-between bg-[#FAF8F5]">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#2D5864]">
                  Libro de Incidencias Biológicas y de Transporte
                </h4>
                <p className="text-[11px] text-neutral-500">
                  Registro de anomalías en precintos, temperaturas o muestras observadas
                </p>
              </div>
            </div>

            {incidencias.length === 0 ? (
              <div className="p-8 text-center text-neutral-400 text-xs">
                No se registran incidencias activas en el circuito de derivación.
              </div>
            ) : (
              <div className="divide-y divide-neutral-100">
                {incidencias.map(inc => (
                  <div key={inc.id} className="p-4.5 space-y-2 hover:bg-neutral-50/50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-rose-700">{inc.id}</span>
                        <span className="text-neutral-300">·</span>
                        <span className="text-xs font-bold text-neutral-900">{inc.tipo}</span>
                        {inc.remitoId && (
                          <span className="text-xs font-mono text-neutral-500">
                            (Remito: {inc.remitoId})
                          </span>
                        )}
                      </div>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          inc.resuelto ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                        }`}
                      >
                        {inc.resuelto ? 'Resuelta' : 'Pendiente de Resolución'}
                      </span>
                    </div>

                    <p className="text-xs text-neutral-700 leading-relaxed">{inc.descripcion}</p>

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-neutral-400 pt-1 gap-2">
                      <span>
                        Reportado por {inc.responsableReporte} · {inc.fechaHora}
                      </span>

                      {!inc.resuelto ? (
                        <button
                          onClick={() => {
                            setSelectedIncidenciaForResolve(inc.id);
                            setResolucionTexto('Se solicitó nueva extracción al paciente y se notificó al veterinario.');
                          }}
                          className="text-xs font-semibold text-[#2D5864] hover:underline"
                        >
                          Resolver Incidencia
                        </button>
                      ) : (
                        <span className="text-neutral-600 font-medium">
                          Resolución: {inc.resolucion}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: VERIFICAR PRECINTO Y RECEPCIÓN */}
      {selectedRemito && (
        <Modal
          isOpen={isVerificarModalOpen}
          onClose={() => setIsVerificarModalOpen(false)}
          title={`Control de Entrada & Precinto: ${selectedRemito.id}`}
          subtitle={`Contenedor ${selectedRemito.conservadoraId} · Precinto esperado: ${selectedRemito.precintoCodigo}`}
          maxWidth="md"
        >
          <form onSubmit={handleConfirmarRecepcion} className="space-y-4 text-xs">
            <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#F2E8D8] space-y-1.5">
              <span className="text-[11px] text-neutral-400 block font-medium">Información del Despacho</span>
              <div className="text-neutral-800">
                <strong>Clínica de Origen:</strong> {selectedRemito.clinicaOrigen}
              </div>
              <div className="text-neutral-800">
                <strong>Muestras a contrastar:</strong>{' '}
                <span className="font-mono">{selectedRemito.muestrasIds.join(', ')}</span> ({selectedRemito.muestrasIds.length} unidades)
              </div>
            </div>

            {/* Crucial selection: Seal Integrity */}
            <div>
              <label className="block text-neutral-700 font-bold mb-2">
                Estado del Precinto Sanitario #{selectedRemito.precintoCodigo} *
              </label>

              <div className="space-y-2">
                <label className="flex items-start gap-2.5 p-3 rounded-lg border border-emerald-200 bg-emerald-50/50 cursor-pointer hover:bg-emerald-50">
                  <input
                    type="radio"
                    name="estadoPrecinto"
                    value="Integro"
                    checked={verificacionData.estadoPrecinto === 'Integro'}
                    onChange={() => setVerificacionData({ ...verificacionData, estadoPrecinto: 'Integro' })}
                    className="mt-0.5 text-[#2D5864] focus:ring-[#2D5864]"
                  />
                  <div>
                    <span className="font-semibold text-emerald-900 block flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-700" />
                      Precinto Íntegro y Conforme
                    </span>
                    <span className="text-[11px] text-emerald-800 leading-tight block mt-0.5">
                      El cierre de seguridad coincide con el remito y no presenta adulteraciones. Las muestras se aceptan.
                    </span>
                  </div>
                </label>

                <label className="flex items-start gap-2.5 p-3 rounded-lg border border-rose-200 bg-rose-50/50 cursor-pointer hover:bg-rose-50">
                  <input
                    type="radio"
                    name="estadoPrecinto"
                    value="Roto"
                    checked={verificacionData.estadoPrecinto === 'Roto'}
                    onChange={() => setVerificacionData({ ...verificacionData, estadoPrecinto: 'Roto' })}
                    className="mt-0.5 text-rose-600 focus:ring-rose-500"
                  />
                  <div>
                    <span className="font-semibold text-rose-900 block flex items-center gap-1.5">
                      <ShieldAlert className="w-4 h-4 text-rose-700" />
                      Precinto Roto / Violado (Criterio de Rechazo)
                    </span>
                    <span className="text-[11px] text-rose-800 leading-tight block mt-0.5">
                      <strong>Regla de negocio:</strong> Se bloquea el procesamiento y todas las muestras pasan a estado Rechazada.
                    </span>
                  </div>
                </label>

                <label className="flex items-start gap-2.5 p-3 rounded-lg border border-amber-200 bg-amber-50/50 cursor-pointer hover:bg-amber-50">
                  <input
                    type="radio"
                    name="estadoPrecinto"
                    value="CodigoNoCoincide"
                    checked={verificacionData.estadoPrecinto === 'CodigoNoCoincide'}
                    onChange={() => setVerificacionData({ ...verificacionData, estadoPrecinto: 'CodigoNoCoincide' })}
                    className="mt-0.5 text-amber-600 focus:ring-amber-500"
                  />
                  <div>
                    <span className="font-semibold text-amber-900 block">
                      Código de Precinto No Coincide / Ausente
                    </span>
                    <span className="text-[11px] text-amber-800 leading-tight block mt-0.5">
                      Discrepancia en remito. Se genera incidencia para auditoría sanitaria.
                    </span>
                  </div>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">
                Responsable que Realiza la Verificación *
              </label>
              <input
                type="text"
                required
                value={verificacionData.verificadoPor}
                onChange={e => setVerificacionData({ ...verificacionData, verificadoPor: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
              />
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Observaciones de Inspección</label>
              <textarea
                rows={2}
                value={verificacionData.observaciones}
                onChange={e => setVerificacionData({ ...verificacionData, observaciones: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
              <button
                type="button"
                onClick={() => setIsVerificarModalOpen(false)}
                className="px-4 py-2 text-neutral-600"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className={`px-4 py-2 font-semibold text-white rounded-lg transition-colors ${
                  verificacionData.estadoPrecinto === 'Integro'
                    ? 'bg-[#2D5864] hover:bg-[#23454f]'
                    : 'bg-rose-700 hover:bg-rose-800'
                }`}
              >
                {verificacionData.estadoPrecinto === 'Integro'
                  ? 'Confirmar Recepción Conforme'
                  : 'Rechazar Envío y Registrar Incidencia'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* MODAL: CARGAR RESULTADO DE LABORATORIO */}
      <Modal
        isOpen={isCargarResultadoModalOpen}
        onClose={() => setIsCargarResultadoModalOpen(false)}
        title="Incorporar Resultados del Laboratorio"
        subtitle="Vincular informe analítico con la orden médica y la historia clínica"
        maxWidth="lg"
      >
        <form onSubmit={handleGuardarResultado} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Orden de Derivación *</label>
              <select
                value={resultadoData.ordenId}
                onChange={e => setResultadoData({ ...resultadoData, ordenId: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg font-mono"
              >
                {ordenes.map(o => (
                  <option key={o.id} value={o.id}>
                    {o.id} ({o.detalles.length} análisis)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Muestra Analizada *</label>
              <select
                value={resultadoData.muestraId}
                onChange={e => setResultadoData({ ...resultadoData, muestraId: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg font-mono"
              >
                {muestras
                  .filter(m => m.estadoActual === 'Recibida' || m.estadoActual === 'Analizada' || m.estadoActual === 'En tránsito')
                  .map(m => (
                    <option key={m.id} value={m.id}>
                      {m.id} — {m.tipoMaterial} ({m.estadoActual})
                    </option>
                  ))}
              </select>
            </div>
          </div>

          <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#F2E8D8] space-y-3">
            <span className="font-bold text-[#2D5864] uppercase tracking-wider text-[11px] block">
              Determinaciones y Valores Medidos
            </span>

            {/* Row 1 */}
            <div className="grid grid-cols-12 gap-2 items-center">
              <input
                type="text"
                value={resultadoData.param1.parametro}
                onChange={e => setResultadoData({ ...resultadoData, param1: { ...resultadoData.param1, parametro: e.target.value } })}
                className="col-span-4 p-1.5 bg-white border rounded text-xs"
              />
              <input
                type="text"
                value={resultadoData.param1.valor}
                onChange={e => setResultadoData({ ...resultadoData, param1: { ...resultadoData.param1, valor: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded font-mono text-xs font-bold"
              />
              <input
                type="text"
                value={resultadoData.param1.unidad}
                onChange={e => setResultadoData({ ...resultadoData, param1: { ...resultadoData.param1, unidad: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              />
              <input
                type="text"
                value={resultadoData.param1.rango}
                onChange={e => setResultadoData({ ...resultadoData, param1: { ...resultadoData.param1, rango: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              />
              <select
                value={resultadoData.param1.alerta}
                onChange={e => setResultadoData({ ...resultadoData, param1: { ...resultadoData.param1, alerta: e.target.value as any } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              >
                <option value="Normal">Normal</option>
                <option value="Alto">Alto</option>
                <option value="Bajo">Bajo</option>
              </select>
            </div>

            {/* Row 2 */}
            <div className="grid grid-cols-12 gap-2 items-center">
              <input
                type="text"
                value={resultadoData.param2.parametro}
                onChange={e => setResultadoData({ ...resultadoData, param2: { ...resultadoData.param2, parametro: e.target.value } })}
                className="col-span-4 p-1.5 bg-white border rounded text-xs"
              />
              <input
                type="text"
                value={resultadoData.param2.valor}
                onChange={e => setResultadoData({ ...resultadoData, param2: { ...resultadoData.param2, valor: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded font-mono text-xs font-bold"
              />
              <input
                type="text"
                value={resultadoData.param2.unidad}
                onChange={e => setResultadoData({ ...resultadoData, param2: { ...resultadoData.param2, unidad: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              />
              <input
                type="text"
                value={resultadoData.param2.rango}
                onChange={e => setResultadoData({ ...resultadoData, param2: { ...resultadoData.param2, rango: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              />
              <select
                value={resultadoData.param2.alerta}
                onChange={e => setResultadoData({ ...resultadoData, param2: { ...resultadoData.param2, alerta: e.target.value as any } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              >
                <option value="Normal">Normal</option>
                <option value="Alto">Alto</option>
                <option value="Bajo">Bajo</option>
              </select>
            </div>

            {/* Row 3 */}
            <div className="grid grid-cols-12 gap-2 items-center">
              <input
                type="text"
                value={resultadoData.param3.parametro}
                onChange={e => setResultadoData({ ...resultadoData, param3: { ...resultadoData.param3, parametro: e.target.value } })}
                className="col-span-4 p-1.5 bg-white border rounded text-xs"
              />
              <input
                type="text"
                value={resultadoData.param3.valor}
                onChange={e => setResultadoData({ ...resultadoData, param3: { ...resultadoData.param3, valor: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded font-mono text-xs font-bold"
              />
              <input
                type="text"
                value={resultadoData.param3.unidad}
                onChange={e => setResultadoData({ ...resultadoData, param3: { ...resultadoData.param3, unidad: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              />
              <input
                type="text"
                value={resultadoData.param3.rango}
                onChange={e => setResultadoData({ ...resultadoData, param3: { ...resultadoData.param3, rango: e.target.value } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              />
              <select
                value={resultadoData.param3.alerta}
                onChange={e => setResultadoData({ ...resultadoData, param3: { ...resultadoData.param3, alerta: e.target.value as any } })}
                className="col-span-2 p-1.5 bg-white border rounded text-xs"
              >
                <option value="Normal">Normal</option>
                <option value="Alto">Alto</option>
                <option value="Bajo">Bajo</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Conclusión e Interpretación Diagnóstica *</label>
            <textarea
              required
              rows={2}
              value={resultadoData.conclusionDiagnostica}
              onChange={e => setResultadoData({ ...resultadoData, conclusionDiagnostica: e.target.value })}
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
            <button
              type="button"
              onClick={() => setIsCargarResultadoModalOpen(false)}
              className="px-4 py-2 text-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors"
            >
              Guardar y Vincular a Historia Clínica
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: RESOLVER INCIDENCIA */}
      {selectedIncidenciaForResolve && (
        <Modal
          isOpen={!!selectedIncidenciaForResolve}
          onClose={() => setSelectedIncidenciaForResolve(null)}
          title="Resolver Incidencia Sanitaria"
          subtitle={`ID: ${selectedIncidenciaForResolve}`}
          maxWidth="md"
        >
          <form onSubmit={handleResolveIncidencia} className="space-y-4 text-xs">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">
                Acción Correctiva / Resolución Tomada *
              </label>
              <textarea
                required
                rows={3}
                value={resolucionTexto}
                onChange={e => setResolucionTexto(e.target.value)}
                placeholder="Ej. Se notificó al veterinario tratante, se canceló el procesamiento biológico y se coordinó una nueva toma de muestra..."
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
              <button
                type="button"
                onClick={() => setSelectedIncidenciaForResolve(null)}
                className="px-4 py-2 text-neutral-600"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg"
              >
                Cerrar Incidencia
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
