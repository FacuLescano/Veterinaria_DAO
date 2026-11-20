import React, { useEffect, useState } from 'react';
import { useVeterinaria } from '../../context/VeterinariaContext';
import { 
  OrdenAnalisis, 
  MuestraBiologica, 
  TipoAnalisis, 
  TipoMaterialBiologico, 
  CondicionConservacion, 
  EstadoOrden 
} from '../../types/veterinaria';
import { Modal } from '../common/Modal';
import { 
  FlaskConical, 
  Plus, 
  Link2, 
  History, 
  CheckCircle, 
  AlertCircle, 
  Calendar, 
  FileCheck, 
  Thermometer,
  Layers,
  ArrowRight
} from 'lucide-react';

const extraccionInicial = {
  tipoMaterial: 'Sangre con EDTA (Tubo lila)' as TipoMaterialBiologico,
  responsableExtraccion: 'Dra. Sofía Carrizo',
  condicionConservacion: 'Refrigerada (2° a 8°C)' as CondicionConservacion,
  observaciones: ''
};

type ConsultaHistorial =
  | { estado: 'cargando' }
  | { estado: 'listo'; muestra: MuestraBiologica }
  | { estado: 'error'; mensaje: string };

export const Modulo2OrdenesMuestras: React.FC = () => {
  const {
    ordenes,
    muestras,
    mascotas,
    consultas,
    createOrden,
    registrarMuestra,
    consultarMuestraConHistorial,
    vincularMuestraConAnalisis,
    setActiveModule,
    showToast
  } = useVeterinaria();

  const [activeTab, setActiveTab] = useState<'ordenes' | 'muestras'>('ordenes');
  const [muestraHistorialId, setMuestraHistorialId] = useState<string | null>(null);
  const [consultaHistorial, setConsultaHistorial] = useState<ConsultaHistorial>({ estado: 'cargando' });
  const selectedMuestraForTimeline = consultaHistorial.estado === 'listo' ? consultaHistorial.muestra : null;

  // Modals
  const [isNewOrdenModalOpen, setIsNewOrdenModalOpen] = useState(false);
  const [ordenExtraccionId, setOrdenExtraccionId] = useState<string | null>(null);
  const [guardandoExtraccion, setGuardandoExtraccion] = useState(false);
  const [isVincularModalOpen, setIsVincularModalOpen] = useState(false);

  // New Orden Form State
  const [newOrdenData, setNewOrdenData] = useState({
    mascotaId: mascotas[0]?.id || '',
    veterinarioSolicitante: 'Dr. Alejandro Morales',
    prioridad: 'Normal' as 'Normal' | 'Urgente',
    analisisSeleccionados: ['Hemograma Completo'] as TipoAnalisis[],
    indicaciones: ''
  });

  // New Muestra Form State
  const [newMuestraData, setNewMuestraData] = useState(extraccionInicial);

  // Vincular Form State
  const [vincularData, setVincularData] = useState({
    ordenId: '',
    detalleId: '',
    muestraId: ''
  });

  useEffect(() => {
    if (mascotas.length && !mascotas.some((m) => m.id === newOrdenData.mascotaId)) setNewOrdenData((d) => ({ ...d, mascotaId: mascotas[0].id }));
  }, [mascotas, newOrdenData.mascotaId]);

  useEffect(() => {
    if (muestraHistorialId === null) return;
    const consulta = new AbortController();
    consultarMuestraConHistorial(muestraHistorialId, consulta.signal)
      .then(muestra => {
        if (!consulta.signal.aborted) setConsultaHistorial({ estado: 'listo', muestra });
      })
      .catch((error: unknown) => {
        if (!consulta.signal.aborted) {
          setConsultaHistorial({
            estado: 'error',
            mensaje: error instanceof Error ? error.message : 'No se pudo cargar el historial de la muestra.',
          });
        }
      });
    return () => consulta.abort();
  }, [muestraHistorialId, consultarMuestraConHistorial]);

  const muestrasParaVincular = muestras.filter(m => m.ordenId === vincularData.ordenId && m.estadoActual === 'Extraída');

  // Handlers
  const handleCreateOrden = async (e: React.FormEvent) => {
    e.preventDefault();
    const now = new Date().toISOString().replace('T', ' ').substring(0, 16);
    // Find or create a consultation reference
    const latestConsulta = consultas.find(c => c.mascotaId === newOrdenData.mascotaId);

    const detalles = newOrdenData.analisisSeleccionados.map((tipo, idx) => ({
      id: `DET-${Date.now().toString().slice(-4)}-${idx}`,
      tipoAnalisis: tipo,
      indicaciones: newOrdenData.indicaciones || 'Solicitado por veterinario clínico.',
      estado: 'Pendiente de muestra' as const
    }));

    try {
    await createOrden({
      consultaId: latestConsulta ? latestConsulta.id : 'CON-ESPONTANEA',
      mascotaId: newOrdenData.mascotaId,
      veterinarioSolicitante: newOrdenData.veterinarioSolicitante,
      fechaSolicitud: now,
      prioridad: newOrdenData.prioridad,
      estado: 'Solicitada',
      detalles
    });

    setIsNewOrdenModalOpen(false);
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo crear la orden', description: error instanceof Error ? error.message : 'Verificá la API y los datos.' });
    }
  };

  const handleRegistrarMuestra = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ordenExtraccionId || guardandoExtraccion) return;
    setGuardandoExtraccion(true);
    try {
      await registrarMuestra({ ...newMuestraData, ordenId: ordenExtraccionId });
      setOrdenExtraccionId(null);
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo registrar la muestra', description: error instanceof Error ? error.message : 'Verificá la API y los datos.' });
    } finally {
      setGuardandoExtraccion(false);
    }
  };

  const handleVincularMuestra = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vincularData.ordenId || !vincularData.detalleId || !vincularData.muestraId) return;

    try {
      await vincularMuestraConAnalisis(vincularData.ordenId, vincularData.detalleId, vincularData.muestraId);
      setIsVincularModalOpen(false);
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo vincular la muestra', description: error instanceof Error ? error.message : 'Verificá la API y los datos.' });
    }
  };

  const openVincularForOrden = (ord: OrdenAnalisis) => {
    const unlinkedDetalle = ord.detalles.find(d => !d.muestraAsociadaId);
    setVincularData({
      ordenId: ord.id,
      detalleId: unlinkedDetalle ? unlinkedDetalle.id : (ord.detalles[0]?.id || ''),
      muestraId: muestras.find((m) => m.ordenId === ord.id && m.estadoActual === 'Extraída')?.id || ''
    });
    setIsVincularModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Top Segmented Tabs & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E7E2DA] pb-4">
        <div className="inline-flex items-center p-1 bg-[#FAF6EF] border border-[#E7E2DA] rounded-xl">
          <button
            onClick={() => setActiveTab('ordenes')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'ordenes'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Órdenes de Derivación ({ordenes.length})
          </button>
          <button
            onClick={() => setActiveTab('muestras')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === 'muestras'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Muestras Biológicas & Trazabilidad ({muestras.length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsNewOrdenModalOpen(true)}
            className="px-3 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Emitir Nueva Orden</span>
          </button>
        </div>
      </div>

      {/* TAB 1: ÓRDENES DE ANÁLISIS */}
      {activeTab === 'ordenes' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {ordenes.map(ord => {
              const pet = mascotas.find(m => m.id === ord.mascotaId);
              const unlinkedCount = ord.detalles.filter(d => !d.muestraAsociadaId).length;
              const muestrasDeOrden = muestras.filter(m => m.ordenId === ord.id);

              return (
                <div
                  key={ord.id}
                  className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4"
                >
                  {/* Order Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-neutral-100 pb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-[#FAF6EF] rounded-lg text-[#2D5864]">
                        <FileCheck className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-bold text-[#2D5864]">{ord.id}</span>
                          <span className="text-neutral-300">·</span>
                          <h4 className="font-bold text-sm text-neutral-900">
                            Paciente: {pet?.nombre} ({pet?.especie} · {pet?.raza})
                          </h4>
                          {ord.prioridad === 'Urgente' && (
                            <span className="text-[10px] font-bold text-rose-700 bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded">
                              URGENTE
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-neutral-500 mt-0.5">
                          Solicitó {ord.veterinarioSolicitante} · {ord.fechaSolicitud}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-medium text-neutral-600 bg-neutral-100 px-2 py-1 rounded">
                        Estado: {ord.estado}
                      </span>
                      <button
                        type="button"
                        disabled={ord.estado === 'Cancelada'}
                        onClick={() => {
                          setNewMuestraData(extraccionInicial);
                          setOrdenExtraccionId(ord.id);
                        }}
                        className="px-2.5 py-1 text-xs font-semibold text-[#2D5864] border border-[#2D5864]/30 rounded-md hover:bg-[#FAF6EF] disabled:opacity-50 flex items-center gap-1"
                      >
                        <FlaskConical className="w-3.5 h-3.5" />
                        Registrar extracción de muestra
                      </button>
                      {unlinkedCount > 0 && muestrasDeOrden.some(m => m.estadoActual === 'Extraída') && (
                        <button
                          onClick={() => openVincularForOrden(ord)}
                          className="px-2.5 py-1 text-xs font-semibold text-[#5F8E9C] hover:text-[#2D5864] bg-[#FAF8F5] border border-[#F2E8D8] rounded-md transition-colors flex items-center gap-1"
                        >
                          <Link2 className="w-3.5 h-3.5" />
                          <span>Asignar muestra a estudio ({unlinkedCount} pendiente)</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Requested Tests & Assigned Samples */}
                  {muestrasDeOrden.length > 0 && (
                    <div className="text-xs text-neutral-600">
                      <p className="font-semibold">Muestras de esta orden</p>
                      <ul className="mt-1 space-y-1">
                        {muestrasDeOrden.map(m => (
                          <li key={m.id} className="break-words">{m.tipoMaterial} · <span className="font-mono">{m.identificacionFisica}</span></li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-neutral-500">
                      Estudios Solicitados en esta Orden ({ord.detalles.length})
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {ord.detalles.map(det => {
                        const muestraVinculada = muestras.find(m => m.id === det.muestraAsociadaId);

                        return (
                          <div
                            key={det.id}
                            className="p-3 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between font-semibold text-neutral-800">
                              <span>{det.tipoAnalisis}</span>
                              <span
                                className={`text-[11px] font-mono px-1.5 py-0.5 rounded ${
                                  det.estado === 'Resultado listo'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : det.muestraAsociadaId
                                    ? 'bg-sky-100 text-sky-800'
                                    : 'bg-amber-100 text-amber-800'
                                }`}
                              >
                                {det.estado}
                              </span>
                            </div>

                            <p className="text-neutral-500 text-[11px]">{det.indicaciones}</p>

                            <div className="pt-1.5 border-t border-neutral-200/50 flex items-center justify-between text-[11px]">
                              {muestraVinculada ? (
                                <div className="flex items-center gap-1.5 text-neutral-700">
                                  <FlaskConical className="w-3 h-3 text-[#2D5864]" />
                                  <span>Muestra:</span>
                                  <span className="font-mono font-semibold text-[#2D5864]">
                                    {muestraVinculada.id} ({muestraVinculada.identificacionFisica})
                                  </span>
                                </div>
                              ) : (
                                <span className="text-amber-700 italic">Sin muestra asignada aún</span>
                              )}

                              {det.estado === 'Resultado listo' && (
                                <button
                                  onClick={() => setActiveModule('recepcion')}
                                  className="text-emerald-700 hover:underline font-semibold flex items-center gap-1"
                                >
                                  <span>Ver Resultado</span>
                                  <ArrowRight className="w-3 h-3" />
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: MUESTRAS BIOLÓGICAS & TRAZABILIDAD */}
      {activeTab === 'muestras' && (
        <div className="space-y-4">
          <div className="bg-white border border-[#E7E2DA] rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 border-b border-[#F2E8D8] flex items-center justify-between bg-[#FAF8F5]">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#2D5864]">
                  Muestras Biológicas Registradas
                </h4>
                <p className="text-[11px] text-neutral-500">
                  Registro inmutable de trazabilidad: Extraída → Empaquetada → En tránsito → Recibida / Rechazada
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-neutral-50 text-neutral-500 border-b border-neutral-200">
                  <tr>
                    <th className="py-2.5 px-4 font-semibold">ID Muestra</th>
                    <th className="py-2.5 px-4 font-semibold">Código Tubo / Rótulo</th>
                    <th className="py-2.5 px-4 font-semibold">Material Biológico</th>
                    <th className="py-2.5 px-4 font-semibold">Extracción</th>
                    <th className="py-2.5 px-4 font-semibold">Conservación</th>
                    <th className="py-2.5 px-4 font-semibold">Estado Actual</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Cadena de Custodia</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {muestras.map(m => {
                    return (
                      <tr key={m.id} className="hover:bg-neutral-50/70 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-[#2D5864] whitespace-nowrap">
                          {m.id}
                        </td>
                        <td className="py-3 px-4 font-mono text-neutral-800">
                          {m.identificacionFisica}
                        </td>
                        <td className="py-3 px-4 text-neutral-700">
                          {m.tipoMaterial}
                        </td>
                        <td className="py-3 px-4 text-neutral-500 whitespace-nowrap">
                          {m.fechaHoraExtraccion}
                          <span className="block text-[11px] text-neutral-400">por {m.responsableExtraccion}</span>
                        </td>
                        <td className="py-3 px-4 text-neutral-600 whitespace-nowrap">
                          <span className="inline-flex items-center gap-1">
                            <Thermometer className="w-3 h-3 text-[#5F8E9C]" />
                            {m.condicionConservacion}
                          </span>
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span
                            className={`inline-flex text-[11px] font-medium px-2 py-0.5 rounded-md ${
                              m.estadoActual === 'Rechazada'
                                ? 'bg-rose-100 text-rose-800 border border-rose-200 font-bold'
                                : m.estadoActual === 'Analizada'
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                : m.estadoActual === 'Recibida'
                                ? 'bg-sky-100 text-sky-800 border border-sky-200'
                                : m.estadoActual === 'En tránsito'
                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                : 'bg-neutral-100 text-neutral-700'
                            }`}
                          >
                            {m.estadoActual}
                          </span>
                          {m.motivoRechazo && (
                            <span className="block text-[10px] text-rose-600 max-w-[150px] truncate" title={m.motivoRechazo}>
                              {m.motivoRechazo}
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right whitespace-nowrap">
                          <button
                            onClick={() => {
                              setConsultaHistorial({ estado: 'cargando' });
                              setMuestraHistorialId(m.id);
                            }}
                            className="px-2.5 py-1 text-xs font-semibold text-[#2D5864] hover:bg-[#FAF6EF] border border-[#2D5864]/20 rounded-md transition-colors inline-flex items-center gap-1"
                          >
                            <History className="w-3.5 h-3.5" />
                            <span>Ver historial</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: EMITIR NUEVA ORDEN */}
      <Modal
        isOpen={isNewOrdenModalOpen}
        onClose={() => setIsNewOrdenModalOpen(false)}
        title="Emitir Orden de Derivación de Laboratorio"
        subtitle="Formalizar solicitud de estudios biológicos para enviar al laboratorio central"
        maxWidth="lg"
      >
        <form onSubmit={handleCreateOrden} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Paciente *</label>
              <select
                value={newOrdenData.mascotaId}
                onChange={e => setNewOrdenData({ ...newOrdenData, mascotaId: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              >
                {mascotas.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.nombre} ({m.especie} - {m.raza})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Veterinario Solicitante</label>
              <input
                type="text"
                value={newOrdenData.veterinarioSolicitante}
                onChange={e => setNewOrdenData({ ...newOrdenData, veterinarioSolicitante: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Prioridad del Estudio</label>
            <select
              value={newOrdenData.prioridad}
              onChange={e => setNewOrdenData({ ...newOrdenData, prioridad: e.target.value as any })}
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            >
              <option value="Normal">Normal (24 a 48 hs)</option>
              <option value="Urgente">Urgente (Procesamiento prioritario)</option>
            </select>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">
              Estudios a Solicitar (Selecciona uno o varios) *
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 bg-[#FAF8F5] border border-[#F2E8D8] rounded-xl">
              {[
                'Hemograma Completo',
                'Perfil Bioquímico Hepático',
                'Perfil Renal (Urea y Creatinina)',
                'Orina Completa y Sedimento',
                'Coproparasitológico Seriado',
                'Citología Cutánea / PAAF',
                'Dosaje Hormonal (T4 / Cortisol)'
              ].map(tipo => {
                const checked = newOrdenData.analisisSeleccionados.includes(tipo as TipoAnalisis);
                return (
                  <label key={tipo} className="flex items-center gap-2 cursor-pointer text-xs">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={e => {
                        if (e.target.checked) {
                          setNewOrdenData({
                            ...newOrdenData,
                            analisisSeleccionados: [...newOrdenData.analisisSeleccionados, tipo as TipoAnalisis]
                          });
                        } else {
                          setNewOrdenData({
                            ...newOrdenData,
                            analisisSeleccionados: newOrdenData.analisisSeleccionados.filter(t => t !== tipo)
                          });
                        }
                      }}
                      className="w-4 h-4 text-[#2D5864] rounded border-neutral-300 focus:ring-[#2D5864]"
                    />
                    <span className={checked ? 'font-semibold text-[#2D5864]' : 'text-neutral-700'}>
                      {tipo}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Indicaciones Clínicas para el Laboratorio</label>
            <textarea
              rows={2}
              value={newOrdenData.indicaciones}
              onChange={e => setNewOrdenData({ ...newOrdenData, indicaciones: e.target.value })}
              placeholder="Ej. Sospecha de leptospirosis / paciente en ayuno de 12 hs..."
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
            <button
              type="button"
              onClick={() => setIsNewOrdenModalOpen(false)}
              className="px-4 py-2 text-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={newOrdenData.analisisSeleccionados.length === 0}
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors disabled:opacity-50"
            >
              Formalizar Orden
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: REGISTRAR EXTRACCIÓN DE MUESTRA */}
      <Modal
        isOpen={ordenExtraccionId !== null}
        onClose={() => { if (!guardandoExtraccion) setOrdenExtraccionId(null); }}
        title="Registrar Extracción de Muestra Biológica"
        subtitle={`Orden de derivación #${ordenExtraccionId}`}
        maxWidth="lg"
      >
        <form onSubmit={handleRegistrarMuestra} className="space-y-4 text-xs">
          <div>
            <label htmlFor="responsable-extraccion" className="block text-neutral-600 font-medium mb-1">Responsable de Extracción *</label>
            <input
              id="responsable-extraccion"
              type="text"
              required
              value={newMuestraData.responsableExtraccion}
              onChange={e => setNewMuestraData({ ...newMuestraData, responsableExtraccion: e.target.value })}
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Tipo de Material Biológico *</label>
              <select
                value={newMuestraData.tipoMaterial}
                onChange={e => setNewMuestraData({ ...newMuestraData, tipoMaterial: e.target.value as any })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              >
                <option value="Sangre con EDTA (Tubo lila)">Sangre con EDTA (Tubo lila)</option>
                <option value="Suero sanguíneo (Tubo rojo)">Suero sanguíneo (Tubo rojo)</option>
                <option value="Plasma heparinizado">Plasma heparinizado</option>
                <option value="Orina por cistocentesis">Orina por cistocentesis</option>
                <option value="Materia fecal">Materia fecal</option>
                <option value="Biopsia / Tejido en formol">Biopsia / Tejido en formol</option>
                <option value="Raspado cutáneo">Raspado cutáneo</option>
              </select>
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Condición de Conservación *</label>
              <select
                value={newMuestraData.condicionConservacion}
                onChange={e => setNewMuestraData({ ...newMuestraData, condicionConservacion: e.target.value as any })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              >
                <option value="Refrigerada (2° a 8°C)">Refrigerada (2° a 8°C)</option>
                <option value="Congelada (-20°C o menos)">Congelada (-20°C o menos)</option>
                <option value="Temperatura Ambiente (15° a 25°C)">Temperatura Ambiente (15° a 25°C)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Observaciones Iniciales de Calidad</label>
            <input
              type="text"
              value={newMuestraData.observaciones}
              onChange={e => setNewMuestraData({ ...newMuestraData, observaciones: e.target.value })}
              placeholder="Ej. Volumen 3ml, sin hemólisis visible, punción limpia..."
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
            <button
              type="button"
              disabled={guardandoExtraccion}
              onClick={() => setOrdenExtraccionId(null)}
              className="px-4 py-2 text-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={guardandoExtraccion}
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors disabled:opacity-50"
            >
              {guardandoExtraccion ? 'Registrando…' : 'Registrar muestra'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: VINCULAR MUESTRA A DETALLE DE ORDEN */}
      <Modal
        isOpen={isVincularModalOpen}
        onClose={() => setIsVincularModalOpen(false)}
        title="Vincular Muestra con Análisis Solicitado"
        subtitle="Asociar el tubo físico de muestra biológica para satisfacer el estudio de la orden"
        maxWidth="md"
      >
        <form onSubmit={handleVincularMuestra} className="space-y-4 text-xs">
          <div>
            <label className="block text-neutral-600 font-medium mb-1">Orden de Derivación</label>
            <span className="font-mono font-bold text-[#2D5864] block p-2 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8]">
              {vincularData.ordenId}
            </span>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Estudio Solicitado a Vincular *</label>
            <select
              value={vincularData.detalleId}
              onChange={e => setVincularData({ ...vincularData, detalleId: e.target.value })}
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            >
              {ordenes
                .find(o => o.id === vincularData.ordenId)
                ?.detalles.map(d => (
                  <option key={d.id} value={d.id}>
                    {d.tipoAnalisis} ({d.estado})
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Muestra Biológica a Asignar *</label>
            <select
              value={vincularData.muestraId}
              onChange={e => setVincularData({ ...vincularData, muestraId: e.target.value })}
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg font-mono"
            >
              {muestrasParaVincular.map(m => (
                <option key={m.id} value={m.id}>
                  {m.id} — {m.identificacionFisica} ({m.tipoMaterial} · {m.estadoActual})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
            <button
              type="button"
              onClick={() => setIsVincularModalOpen(false)}
              className="px-4 py-2 text-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!muestrasParaVincular.some(m => m.id === vincularData.muestraId)}
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors"
            >
              Confirmar Vinculación
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: HISTORIAL DE TRAZABILIDAD INMUTABLE */}
      {muestraHistorialId !== null && (
        <Modal
          isOpen
          onClose={() => setMuestraHistorialId(null)}
          title={`Cadena de Custodia: ${muestraHistorialId}`}
          subtitle={selectedMuestraForTimeline
            ? `Rótulo: ${selectedMuestraForTimeline.identificacionFisica} · ${selectedMuestraForTimeline.tipoMaterial}`
            : undefined}
          maxWidth="lg"
        >
          <div className="space-y-4 text-xs">
            {consultaHistorial.estado === 'cargando' && (
              <p role="status" className="text-neutral-600">Cargando historial…</p>
            )}
            {consultaHistorial.estado === 'error' && (
              <p role="alert" className="text-rose-700">{consultaHistorial.mensaje}</p>
            )}
            {selectedMuestraForTimeline && (
              <>
                {/* Sample summary */}
                <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#F2E8D8] flex items-center justify-between">
                  <div>
                    <span className="text-neutral-400 block text-[11px]">Condición Térmica:</span>
                    <span className="font-semibold text-neutral-800">{selectedMuestraForTimeline.condicionConservacion}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-neutral-400 block text-[11px]">Estado Actual:</span>
                    <span className="font-bold text-[#2D5864] font-mono">{selectedMuestraForTimeline.estadoActual}</span>
                  </div>
                </div>

                {/* Timeline */}
                <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#E7E2DA]">
                  {selectedMuestraForTimeline.historialTrazabilidad.map(evento => (
                    <div key={evento.id} className="relative group">
                      <div className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-white border-2 border-[#2D5864] flex items-center justify-center">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#2D5864]" />
                      </div>
                      <div className="p-3 bg-white border border-neutral-200 rounded-lg space-y-1">
                        <div className="flex items-center justify-between font-mono text-[11px] text-neutral-500">
                          <span>{evento.fechaHora}</span>
                          <span className="font-semibold text-[#2D5864]">{evento.estadoNuevo}</span>
                        </div>
                        <div className="text-neutral-800 font-medium">
                          {evento.ubicacion}
                        </div>
                        <div className="text-neutral-500 text-[11px]">
                          Responsable: {evento.responsable}
                        </div>
                        {evento.observaciones && (
                          <p className="text-neutral-600 text-[11px] pt-1 border-t border-neutral-100">
                            {evento.observaciones}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                {selectedMuestraForTimeline.historialTrazabilidad.length === 0 && (
                  <p className="text-neutral-600">Esta muestra aún no tiene cambios de estado registrados.</p>
                )}
              </>
            )}

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setMuestraHistorialId(null)}
                className="px-4 py-2 font-medium text-neutral-600 hover:text-neutral-900 border border-neutral-200 rounded-lg"
              >
                Cerrar
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
