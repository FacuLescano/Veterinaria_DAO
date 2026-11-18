import React, { useEffect, useState } from 'react';
import { useVeterinaria } from '../../context/VeterinariaContext';
import { Mascota, Responsable, Turno, ConsultaMedica, Especie, SexoMascota } from '../../types/veterinaria';
import { Modal } from '../common/Modal';
import { 
  Search, 
  Plus, 
  Calendar, 
  FileText, 
  Clock, 
  UserCheck, 
  Activity, 
  ShieldAlert, 
  ChevronRight,
  Stethoscope,
  ArrowRight,
  Camera,
  Upload,
  Image as ImageIcon,
  Pencil
} from 'lucide-react';

export const Modulo1Pacientes: React.FC = () => {
  const {
    responsables,
    mascotas,
    turnos,
    consultas,
    ordenes,
    resultados,
    addResponsable,
    addMascota,
    updateMascota,
    addTurno,
    updateTurnoEstado,
    addConsulta,
    createOrden,
    showToast,
    setActiveModule
  } = useVeterinaria();

  const [subTab, setSubTab] = useState<'mascotas' | 'turnos' | 'consultas'>('mascotas');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMascota, setSelectedMascota] = useState<Mascota | null>(null);

  // Modals state
  const [isNewMascotaModalOpen, setIsNewMascotaModalOpen] = useState(false);
  const [isEditMascotaModalOpen, setIsEditMascotaModalOpen] = useState(false);
  const [editingMascota, setEditingMascota] = useState<Mascota | null>(null);
  const [isNewTurnoModalOpen, setIsNewTurnoModalOpen] = useState(false);
  const [isNewConsultaModalOpen, setIsNewConsultaModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);

  // New Mascota & Responsable Form State
  const [crearNuevoResponsable, setCrearNuevoResponsable] = useState(false);
  const [selectedRespId, setSelectedRespId] = useState(responsables[0]?.id || '');
  const [newRespData, setNewRespData] = useState({
    nombreCompleto: '',
    documento: '',
    telefono: '',
    email: '',
    domicilio: ''
  });
  const [newMascotaData, setNewMascotaData] = useState({
    nombre: '',
    especie: 'Canino' as Especie,
    raza: '',
    sexo: 'Hembra' as SexoMascota,
    fechaNacimientoAprox: '2023-01-01',
    pesoKg: 10.0,
    microchip: '',
    alergias: '',
    fotoUrl: ''
  });

  useEffect(() => {
    if (!responsables.some((r) => r.id === selectedRespId) && responsables.length > 0) {
      setSelectedRespId(responsables[0].id);
    }
  }, [responsables, selectedRespId]);

  // New Turno Form State
  const [newTurnoData, setNewTurnoData] = useState({
    mascotaId: mascotas[0]?.id || '',
    veterinario: 'Dr. Alejandro Morales (M.P. 4812)',
    fecha: new Date().toISOString().split('T')[0],
    hora: '10:30',
    motivo: ''
  });

  // New Consulta Form State
  const [newConsultaData, setNewConsultaData] = useState({
    mascotaId: mascotas[0]?.id || '',
    turnoId: '',
    veterinario: 'Dr. Alejandro Morales',
    motivo: '',
    evaluacionClinica: '',
    diagnosticoPresuntivo: '',
    tratamiento: '',
    vacunaAplicada: '',
    requiereAnalisis: false,
    tipoAnalisisSolicitado: 'Hemograma Completo',
    prioridad: 'Normal' as 'Normal' | 'Urgente'
  });

  useEffect(() => {
    if (mascotas.length && !mascotas.some((m) => m.id === newTurnoData.mascotaId)) setNewTurnoData((d) => ({ ...d, mascotaId: mascotas[0].id }));
    if (mascotas.length && !mascotas.some((m) => m.id === newConsultaData.mascotaId)) setNewConsultaData((d) => ({ ...d, mascotaId: mascotas[0].id }));
  }, [mascotas, newTurnoData.mascotaId, newConsultaData.mascotaId]);

  // Filtering
  const filteredMascotas = mascotas.filter(m => {
    const resp = responsables.find(r => r.id === m.responsableId);
    const search = searchTerm.toLowerCase();
    return (
      m.nombre.toLowerCase().includes(search) ||
      m.raza.toLowerCase().includes(search) ||
      m.especie.toLowerCase().includes(search) ||
      (m.microchip && m.microchip.includes(search)) ||
      (resp && resp.nombreCompleto.toLowerCase().includes(search)) ||
      (resp && resp.documento.includes(search))
    );
  });

  // Handle Mascota Submission
  const handleSaveMascota = async (e: React.FormEvent) => {
    e.preventDefault();
    let respId = selectedRespId;
    if (crearNuevoResponsable) {
      if (!newRespData.nombreCompleto || !newRespData.documento) return;
      try {
        const respCreated = await addResponsable(newRespData);
        respId = respCreated.id;
      } catch (error) {
        showToast({ type: 'error', title: 'No se pudo guardar el responsable', description: error instanceof Error ? error.message : 'Verificá los datos y la conexión con el backend.' });
        return;
      }
    }
    if (!newMascotaData.nombre || !newMascotaData.raza || !respId) return;

    try {
      await addMascota({
        ...newMascotaData,
        responsableId: respId,
        pesoKg: Number(newMascotaData.pesoKg)
      });

      setIsNewMascotaModalOpen(false);
      setNewMascotaData({
        nombre: '', especie: 'Canino', raza: '', sexo: 'Hembra',
        fechaNacimientoAprox: '2023-01-01', pesoKg: 10.0, microchip: '', alergias: '', fotoUrl: ''
      });
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo guardar la mascota', description: error instanceof Error ? error.message : 'Verificá los datos y la conexión con el backend.' });
    }
  };

  // Handle Turno Submission
  const handleSaveTurno = async (e: React.FormEvent) => {
    e.preventDefault();
    const pet = mascotas.find(m => m.id === newTurnoData.mascotaId);
    if (!pet) return;

    const res = await addTurno({
      ...newTurnoData,
      responsableId: pet.responsableId,
      estado: 'Pendiente'
    });

    if (res.success) {
      setIsNewTurnoModalOpen(false);
    }
  };

  // Handle Consulta Submission
  const handleSaveConsulta = async (e: React.FormEvent) => {
    e.preventDefault();
    const now = new Date();
    const hora = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    const fecha = now.toISOString().split('T')[0];

    try {
    const consultaCreated = await addConsulta({
      mascotaId: newConsultaData.mascotaId,
      turnoId: newConsultaData.turnoId || undefined,
      veterinario: newConsultaData.veterinario,
      fecha,
      hora,
      motivo: newConsultaData.motivo,
      evaluacionClinica: newConsultaData.evaluacionClinica,
      diagnosticoPresuntivo: newConsultaData.diagnosticoPresuntivo,
      tratamiento: newConsultaData.tratamiento,
      vacunaAplicada: newConsultaData.vacunaAplicada || undefined,
      requiereAnalisis: newConsultaData.requiereAnalisis
    });

    // If laboratory analysis was requested, automatically emit an Orden de Derivación!
    if (newConsultaData.requiereAnalisis) {
      await createOrden({
        consultaId: consultaCreated.id,
        mascotaId: newConsultaData.mascotaId,
        veterinarioSolicitante: newConsultaData.veterinario,
        fechaSolicitud: `${fecha} ${hora}`,
        prioridad: newConsultaData.prioridad,
        estado: 'Solicitada',
        detalles: [
          {
            id: `DET-${Date.now().toString().slice(-4)}`,
            tipoAnalisis: newConsultaData.tipoAnalisisSolicitado as any,
            indicaciones: `Solicitado en consulta ${consultaCreated.id}: ${newConsultaData.diagnosticoPresuntivo}`,
            estado: 'Pendiente de muestra'
          }
        ]
      });
    }

    setIsNewConsultaModalOpen(false);
    setNewConsultaData({
      mascotaId: mascotas[0]?.id || '',
      turnoId: '',
      veterinario: 'Dr. Alejandro Morales',
      motivo: '',
      evaluacionClinica: '',
      diagnosticoPresuntivo: '',
      tratamiento: '',
      vacunaAplicada: '',
      requiereAnalisis: false,
      tipoAnalisisSolicitado: 'Hemograma Completo',
      prioridad: 'Normal'
    });
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo guardar la consulta', description: error instanceof Error ? error.message : 'Verificá los datos y la conexión con el backend.' });
    }
  };

  const openHistoryForMascota = (m: Mascota) => {
    setSelectedMascota(m);
    setIsHistoryModalOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Sub-navigation tabs & Action buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E7E2DA] pb-4">
        {/* Interactive Segmented Control */}
        <div className="inline-flex items-center p-1 bg-[#FAF6EF] border border-[#E7E2DA] rounded-xl">
          <button
            onClick={() => setSubTab('mascotas')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              subTab === 'mascotas'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Fichas de Pacientes ({mascotas.length})
          </button>
          <button
            onClick={() => setSubTab('turnos')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              subTab === 'turnos'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Agenda de Turnos ({turnos.length})
          </button>
          <button
            onClick={() => setSubTab('consultas')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              subTab === 'consultas'
                ? 'bg-white text-[#2D5864] shadow-xs'
                : 'text-neutral-600 hover:text-[#2D5864]'
            }`}
          >
            Consultas Médicas ({consultas.length})
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {subTab === 'mascotas' && (
            <button
              onClick={() => setIsNewMascotaModalOpen(true)}
              className="px-3 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Registrar Mascota / Responsable</span>
            </button>
          )}

          {subTab === 'turnos' && (
            <button
              onClick={() => setIsNewTurnoModalOpen(true)}
              className="px-3 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Agendar Nuevo Turno</span>
            </button>
          )}

          {subTab === 'consultas' && (
            <button
              onClick={() => setIsNewConsultaModalOpen(true)}
              className="px-3 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <Stethoscope className="w-3.5 h-3.5" />
              <span>Registrar Consulta Médica</span>
            </button>
          )}
        </div>
      </div>

      {/* TAB 1: PACIENTES / MASCOTAS */}
      {subTab === 'mascotas' && (
        <div className="space-y-4">
          {/* Search Bar */}
          <div className="relative max-w-md">
            <Search className="w-4 h-4 text-[#8C8C91] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Buscar por nombre, especie, chip o responsable..."
              className="w-full pl-9 pr-4 py-2 text-xs bg-white border border-[#E7E2DA] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#2D5864]/20 focus:border-[#2D5864] transition-all"
            />
          </div>

          {/* Pacientes List */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredMascotas.map(pet => {
              const resp = responsables.find(r => r.id === pet.responsableId);
              const petConsultas = consultas.filter(c => c.mascotaId === pet.id);
              const petOrdenes = ordenes.filter(o => o.mascotaId === pet.id);

              return (
                <div
                  key={pet.id}
                  className="bg-white border border-[#E7E2DA] rounded-xl p-4.5 hover:border-[#5F8E9C]/50 hover:shadow-xs transition-all flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        {pet.fotoUrl ? (
                          <img
                            src={pet.fotoUrl}
                            alt={pet.nombre}
                            className="w-12 h-12 rounded-xl object-cover border border-[#E7E2DA] shrink-0 shadow-2xs"
                          />
                        ) : (
                          <div className="w-12 h-12 rounded-xl bg-[#FAF6EF] text-[#2D5864] flex items-center justify-center font-bold text-sm shrink-0 border border-[#F2E8D8]">
                            {pet.nombre.slice(0, 2).toUpperCase()}
                          </div>
                        )}
                        <div className="min-w-0">
                          <h4 className="font-bold text-neutral-900 text-sm tracking-tight flex items-center gap-2 truncate">
                            {pet.nombre}
                            <span className="text-[11px] font-normal text-[#8C8C91] shrink-0">
                              ({pet.especie} · {pet.sexo})
                            </span>
                          </h4>
                          <p className="text-xs text-neutral-500 mt-0.5 truncate">{pet.raza}</p>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono text-[#8C8C91] bg-neutral-100 px-1.5 py-0.5 rounded shrink-0">
                        {pet.id}
                      </span>
                    </div>

                    {/* Unboxed Metadata */}
                    <div className="text-xs text-neutral-600 space-y-1 pt-1 border-t border-neutral-100">
                      <div className="flex items-center justify-between">
                        <span className="text-neutral-400">Peso actual:</span>
                        <span className="font-medium tabular-nums">{pet.pesoKg} kg</span>
                      </div>
                      {pet.microchip && (
                        <div className="flex items-center justify-between">
                          <span className="text-neutral-400">Microchip:</span>
                          <span className="font-mono text-[11px]">{pet.microchip}</span>
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <span className="text-neutral-400">Responsable:</span>
                        <span className="font-medium text-[#2D5864] truncate max-w-[160px]">
                          {resp?.nombreCompleto || 'Sin asignar'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-neutral-400">Contacto:</span>
                        <span className="font-mono text-[11px] text-neutral-500">{resp?.telefono}</span>
                      </div>
                    </div>

                    {pet.alergias && (
                      <div className="text-[11px] text-amber-800 bg-amber-50/80 p-2 rounded-lg border border-amber-200/50">
                        <span className="font-semibold">Alerta:</span> {pet.alergias}
                      </div>
                    )}
                  </div>

                  <div className="pt-3 mt-3 border-t border-neutral-100 flex items-center justify-between">
                    <span className="text-[11px] text-neutral-400">
                      {petConsultas.length} consultas · {petOrdenes.length} análisis
                    </span>
                    <div className="flex items-center gap-2.5">
                      <button
                        onClick={() => {
                          setEditingMascota(pet);
                          setIsEditMascotaModalOpen(true);
                        }}
                        className="text-xs font-semibold text-neutral-500 hover:text-[#2D5864] flex items-center gap-1 transition-colors px-2 py-1 rounded hover:bg-neutral-100"
                        title="Editar datos de la mascota"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                        <span>Editar</span>
                      </button>
                      <button
                        onClick={() => openHistoryForMascota(pet)}
                        className="text-xs font-semibold text-[#2D5864] hover:text-[#5F8E9C] flex items-center gap-1 transition-colors"
                      >
                        <span>Historia Clínica</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {filteredMascotas.length === 0 && (
            <div className="p-8 text-center bg-white border border-dashed border-neutral-200 rounded-xl text-neutral-500 text-xs">
              No se encontraron pacientes que coincidan con &ldquo;{searchTerm}&rdquo;.
            </div>
          )}
        </div>
      )}

      {/* TAB 2: AGENDA DE TURNOS */}
      {subTab === 'turnos' && (
        <div className="space-y-4">
          <div className="bg-white border border-[#E7E2DA] rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 border-b border-[#F2E8D8] flex items-center justify-between bg-[#FAF8F5]">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#2D5864]">
                  Programación y Agenda Médica
                </h4>
                <p className="text-[11px] text-neutral-500">
                  Control estricto de superposición de turnos para profesionales veterinarios
                </p>
              </div>
              <span className="text-xs font-mono text-neutral-600 bg-white px-2 py-1 rounded border border-neutral-200">
                {turnos.length} turnos registrados
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-neutral-50 text-neutral-500 border-b border-neutral-200">
                  <tr>
                    <th className="py-2.5 px-4 font-semibold">Fecha & Hora</th>
                    <th className="py-2.5 px-4 font-semibold">Paciente</th>
                    <th className="py-2.5 px-4 font-semibold">Responsable</th>
                    <th className="py-2.5 px-4 font-semibold">Veterinario</th>
                    <th className="py-2.5 px-4 font-semibold">Motivo</th>
                    <th className="py-2.5 px-4 font-semibold">Estado</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {turnos.map(turno => {
                    const pet = mascotas.find(m => m.id === turno.mascotaId);
                    const resp = responsables.find(r => r.id === turno.responsableId);

                    return (
                      <tr key={turno.id} className="hover:bg-neutral-50/70 transition-colors">
                        <td className="py-3 px-4 font-mono font-medium text-neutral-900 whitespace-nowrap">
                          {turno.fecha} · <span className="text-[#2D5864] font-bold">{turno.hora}</span>
                        </td>
                        <td className="py-3 px-4 font-semibold text-neutral-800">
                          {pet?.nombre || 'Paciente'}
                        </td>
                        <td className="py-3 px-4 text-neutral-600">
                          {resp?.nombreCompleto || 'Cliente'}
                        </td>
                        <td className="py-3 px-4 text-neutral-700">
                          {turno.veterinario}
                        </td>
                        <td className="py-3 px-4 text-neutral-600 max-w-xs truncate">
                          {turno.motivo}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span
                            className={`inline-flex text-[11px] font-medium px-2 py-0.5 rounded-md ${
                              turno.estado === 'Confirmado'
                                ? 'bg-sky-50 text-sky-800 border border-sky-200'
                                : turno.estado === 'Atendido'
                                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                                : turno.estado === 'Cancelado'
                                ? 'bg-neutral-100 text-neutral-600'
                                : 'bg-amber-50 text-amber-800 border border-amber-200'
                            }`}
                          >
                            {turno.estado}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right space-x-2 whitespace-nowrap">
                          {turno.estado !== 'Atendido' && turno.estado !== 'Cancelado' && (
                            <>
                              <button
                                onClick={() => {
                                  setNewConsultaData(prev => ({
                                    ...prev,
                                    mascotaId: turno.mascotaId,
                                    motivo: turno.motivo,
                                    veterinario: turno.veterinario.split('(')[0].trim()
                                  }));
                                  setIsNewConsultaModalOpen(true);
                                }}
                                className="text-xs font-semibold text-[#2D5864] hover:underline"
                              >
                                Atender
                              </button>
                              <span className="text-neutral-300">·</span>
                              <button
                                onClick={() => void updateTurnoEstado(turno.id, 'Cancelado')}
                                className="text-xs text-rose-600 hover:underline"
                              >
                                Cancelar
                              </button>
                            </>
                          )}
                          {turno.estado === 'Atendido' && (
                            <span className="text-[11px] text-emerald-700 font-medium">✓ Completado</span>
                          )}
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

      {/* TAB 3: CONSULTAS MÉDICAS */}
      {subTab === 'consultas' && (
        <div className="space-y-4">
          <div className="space-y-3">
            {consultas.map(c => {
              const pet = mascotas.find(m => m.id === c.mascotaId);
              const resp = pet ? responsables.find(r => r.id === pet.responsableId) : null;
              const ordenAsociada = ordenes.find(o => o.consultaId === c.id);

              return (
                <div key={c.id} className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-neutral-100 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-[#2D5864]">{c.id}</span>
                        <span aria-hidden="true" className="text-neutral-300">·</span>
                        <h4 className="font-bold text-sm text-neutral-900">
                          {pet?.nombre} ({pet?.especie}) — Responsable: {resp?.nombreCompleto}
                        </h4>
                      </div>
                      <p className="text-xs text-neutral-500 mt-0.5">
                        Atendido por {c.veterinario} · {c.fecha} {c.hora}
                      </p>
                    </div>

                    {c.requiereAnalisis && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-[#5F8E9C] bg-[#FAF6EF] px-2.5 py-1 rounded-md border border-[#F2E8D8]">
                          Derivación de Lab Emitida
                        </span>
                        {ordenAsociada && (
                          <button
                            onClick={() => setActiveModule('ordenes')}
                            className="text-xs font-medium text-[#2D5864] hover:underline flex items-center gap-1"
                          >
                            <span>Ver {ordenAsociada.id}</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="space-y-1.5">
                      <div>
                        <span className="font-semibold text-neutral-700 block">Motivo de consulta:</span>
                        <p className="text-neutral-600 leading-relaxed">{c.motivo}</p>
                      </div>
                      <div>
                        <span className="font-semibold text-neutral-700 block">Examen y Hallazgos Clínicos:</span>
                        <p className="text-neutral-600 leading-relaxed">{c.evaluacionClinica}</p>
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <div>
                        <span className="font-semibold text-neutral-700 block">Diagnóstico Presuntivo:</span>
                        <p className="text-[#2D5864] font-medium leading-relaxed">{c.diagnosticoPresuntivo}</p>
                      </div>
                      <div>
                        <span className="font-semibold text-neutral-700 block">Tratamiento e Indicaciones:</span>
                        <p className="text-neutral-600 leading-relaxed">{c.tratamiento}</p>
                      </div>
                      {c.vacunaAplicada && (
                        <div className="text-[11px] text-emerald-800 bg-emerald-50/70 p-1.5 rounded border border-emerald-200/50">
                          <strong>Vacunación:</strong> {c.vacunaAplicada}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* MODAL: REGISTRAR MASCOTA / RESPONSABLE */}
      <Modal
        isOpen={isNewMascotaModalOpen}
        onClose={() => setIsNewMascotaModalOpen(false)}
        title="Ficha Médica: Nueva Mascota"
        subtitle="Registrar paciente y vincularlo con su responsable"
        maxWidth="xl"
      >
        <form onSubmit={handleSaveMascota} className="space-y-4 text-xs">
          {/* Responsable Section */}
          <div className="p-3.5 bg-[#FAF8F5] rounded-xl border border-[#F2E8D8] space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-[#2D5864] uppercase tracking-wider text-[11px]">
                1. Datos del Responsable
              </span>
              <button
                type="button"
                onClick={() => setCrearNuevoResponsable(!crearNuevoResponsable)}
                className="text-xs font-semibold text-[#5F8E9C] hover:underline"
              >
                {crearNuevoResponsable ? 'Elegir existente' : '+ Crear nuevo responsable'}
              </button>
            </div>

            {!crearNuevoResponsable ? (
              <div>
                <label className="block text-neutral-600 font-medium mb-1">
                  Seleccionar Responsable Existente:
                </label>
                <select
                  value={selectedRespId}
                  onChange={e => setSelectedRespId(e.target.value)}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs focus:ring-2 focus:ring-[#2D5864]/20 focus:border-[#2D5864]"
                >
                  {responsables.map(r => (
                    <option key={r.id} value={r.id}>
                      {r.nombreCompleto} — DNI: {r.documento} ({r.telefono})
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-neutral-600 font-medium mb-1">Nombre Completo *</label>
                  <input
                    type="text"
                    required
                    value={newRespData.nombreCompleto}
                    onChange={e => setNewRespData({ ...newRespData, nombreCompleto: e.target.value })}
                    placeholder="Ej. Juan Pérez"
                    className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block text-neutral-600 font-medium mb-1">DNI / Identificador *</label>
                  <input
                    type="text"
                    required
                    value={newRespData.documento}
                    onChange={e => setNewRespData({ ...newRespData, documento: e.target.value })}
                    placeholder="Ej. 34.123.456"
                    className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block text-neutral-600 font-medium mb-1">Teléfono</label>
                  <input
                    type="text"
                    value={newRespData.telefono}
                    onChange={e => setNewRespData({ ...newRespData, telefono: e.target.value })}
                    placeholder="+54 9 351..."
                    className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block text-neutral-600 font-medium mb-1">Email</label>
                  <input
                    type="email"
                    value={newRespData.email}
                    onChange={e => setNewRespData({ ...newRespData, email: e.target.value })}
                    placeholder="correo@ejemplo.com"
                    className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Mascota Data */}
          <div className="space-y-3 pt-1">
            <span className="font-bold text-[#2D5864] uppercase tracking-wider text-[11px] block">
              2. Ficha de la Mascota (Paciente)
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-neutral-600 font-medium mb-1">Nombre de la Mascota *</label>
                <input
                  type="text"
                  required
                  value={newMascotaData.nombre}
                  onChange={e => setNewMascotaData({ ...newMascotaData, nombre: e.target.value })}
                  placeholder="Ej. Rocky"
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Especie</label>
                <select
                  value={newMascotaData.especie}
                  onChange={e => setNewMascotaData({ ...newMascotaData, especie: e.target.value as Especie })}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                >
                  <option value="Canino">Canino</option>
                  <option value="Felino">Felino</option>
                  <option value="Otro">Otro animal de compañía</option>
                </select>
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Raza *</label>
                <input
                  type="text"
                  required
                  value={newMascotaData.raza}
                  onChange={e => setNewMascotaData({ ...newMascotaData, raza: e.target.value })}
                  placeholder="Ej. Labrador / Mestizo / Siamés"
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Sexo</label>
                <select
                  value={newMascotaData.sexo}
                  onChange={e => setNewMascotaData({ ...newMascotaData, sexo: e.target.value as SexoMascota })}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                >
                  <option value="Macho">Macho</option>
                  <option value="Hembra">Hembra</option>
                </select>
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Peso Aproximado (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  value={newMascotaData.pesoKg}
                  onChange={e => setNewMascotaData({ ...newMascotaData, pesoKg: parseFloat(e.target.value) || 0 })}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Código de Microchip (Opcional)</label>
                <input
                  type="text"
                  value={newMascotaData.microchip}
                  onChange={e => setNewMascotaData({ ...newMascotaData, microchip: e.target.value })}
                  placeholder="15 dígitos"
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs font-mono"
                />
              </div>
            </div>

            {/* Fotografía de la Mascota */}
            <div className="bg-[#FAF8F5] p-3 rounded-xl border border-[#E7E2DA]">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-neutral-700 font-semibold text-xs flex items-center gap-1.5">
                  <Camera className="w-3.5 h-3.5 text-[#2D5864]" />
                  Fotografía de la Mascota
                </label>
                {newMascotaData.fotoUrl && (
                  <button
                    type="button"
                    onClick={() => setNewMascotaData({ ...newMascotaData, fotoUrl: '' })}
                    className="text-[11px] text-rose-600 hover:underline font-medium"
                  >
                    Eliminar foto
                  </button>
                )}
              </div>

              <div className="flex items-center gap-3">
                {newMascotaData.fotoUrl ? (
                  <img
                    src={newMascotaData.fotoUrl}
                    alt="Previsualización"
                    className="w-14 h-14 rounded-xl object-cover border-2 border-[#2D5864] shadow-xs shrink-0"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-xl bg-neutral-200/80 border border-neutral-300 flex items-center justify-center text-neutral-400 shrink-0">
                    <ImageIcon className="w-6 h-6 text-neutral-400" />
                  </div>
                )}

                <div className="flex-1 space-y-1">
                  <label className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#2D5864] hover:bg-[#23454f] text-white rounded-lg text-xs font-medium cursor-pointer transition-colors shadow-2xs">
                    <Upload className="w-3.5 h-3.5" />
                    <span>Subir imagen desde equipo</span>
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          const reader = new FileReader();
                          reader.onloadend = () => {
                            setNewMascotaData({
                              ...newMascotaData,
                              fotoUrl: reader.result as string
                            });
                          };
                          reader.readAsDataURL(file);
                        }
                      }}
                    />
                  </label>
                  <p className="text-[10px] text-neutral-500">
                    Soporta archivos JPG, PNG, WebP de cualquier tamaño.
                  </p>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Alergias o Condiciones Previas</label>
              <input
                type="text"
                value={newMascotaData.alergias}
                onChange={e => setNewMascotaData({ ...newMascotaData, alergias: e.target.value })}
                placeholder="Ej. Reacción a penicilina, intolerancia dietaria..."
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
            <button
              type="button"
              onClick={() => setIsNewMascotaModalOpen(false)}
              className="px-4 py-2 text-neutral-600 hover:text-neutral-900"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors"
            >
              Guardar Ficha
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: EDITAR MASCOTA */}
      {editingMascota && (
        <Modal
          isOpen={isEditMascotaModalOpen}
          onClose={() => setIsEditMascotaModalOpen(false)}
          title={`Editar Ficha: ${editingMascota.nombre}`}
          subtitle={`ID Paciente: ${editingMascota.id}`}
          maxWidth="lg"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void updateMascota(editingMascota.id, editingMascota)
                .then(() => setIsEditMascotaModalOpen(false))
                .catch((error: unknown) => showToast({ type: 'error', title: 'No se pudo actualizar la mascota', description: error instanceof Error ? error.message : 'Verificá los datos y la conexión con el backend.' }));
            }}
            className="space-y-4 text-xs"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-neutral-600 font-medium mb-1">Nombre *</label>
                <input
                  type="text"
                  required
                  value={editingMascota.nombre}
                  onChange={e => setEditingMascota({ ...editingMascota, nombre: e.target.value })}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Especie</label>
                <select
                  value={editingMascota.especie}
                  onChange={e => setEditingMascota({ ...editingMascota, especie: e.target.value as Especie })}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                >
                  <option value="Canino">Canino</option>
                  <option value="Felino">Felino</option>
                  <option value="Otro">Otro animal de compañía</option>
                </select>
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Raza *</label>
                <input
                  type="text"
                  required
                  value={editingMascota.raza}
                  onChange={e => setEditingMascota({ ...editingMascota, raza: e.target.value })}
                  placeholder="Ej. Mestizo, Siamés..."
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Sexo</label>
                <select
                  value={editingMascota.sexo}
                  onChange={e => setEditingMascota({ ...editingMascota, sexo: e.target.value as SexoMascota })}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                >
                  <option value="Macho">Macho</option>
                  <option value="Hembra">Hembra</option>
                </select>
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Peso (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  value={editingMascota.pesoKg}
                  onChange={e => setEditingMascota({ ...editingMascota, pesoKg: parseFloat(e.target.value) || 0 })}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-neutral-600 font-medium mb-1">Microchip (Opcional)</label>
                <input
                  type="text"
                  value={editingMascota.microchip || ''}
                  onChange={e => setEditingMascota({ ...editingMascota, microchip: e.target.value })}
                  className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs font-mono"
                />
              </div>
            </div>

            {/* Fotografía de la Mascota */}
            <div className="bg-[#FAF8F5] p-3 rounded-xl border border-[#E7E2DA]">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-neutral-700 font-semibold text-xs flex items-center gap-1.5">
                  <Camera className="w-3.5 h-3.5 text-[#2D5864]" />
                  Fotografía de la Mascota
                </label>
                {editingMascota.fotoUrl && (
                  <button
                    type="button"
                    onClick={() => setEditingMascota({ ...editingMascota, fotoUrl: '' })}
                    className="text-[11px] text-rose-600 hover:underline font-medium"
                  >
                    Eliminar foto
                  </button>
                )}
              </div>

              <div className="flex items-center gap-3">
                {editingMascota.fotoUrl ? (
                  <img
                    src={editingMascota.fotoUrl}
                    alt="Previsualización"
                    className="w-14 h-14 rounded-xl object-cover border-2 border-[#2D5864] shadow-xs shrink-0"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-xl bg-neutral-200/80 border border-neutral-300 flex items-center justify-center text-neutral-400 shrink-0">
                    <ImageIcon className="w-6 h-6 text-neutral-400" />
                  </div>
                )}

                <div className="flex-1 space-y-1">
                  <label className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#2D5864] hover:bg-[#23454f] text-white rounded-lg text-xs font-medium cursor-pointer transition-colors shadow-2xs">
                    <Upload className="w-3.5 h-3.5" />
                    <span>Cambiar imagen</span>
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          const reader = new FileReader();
                          reader.onloadend = () => {
                            setEditingMascota({
                              ...editingMascota,
                              fotoUrl: reader.result as string
                            });
                          };
                          reader.readAsDataURL(file);
                        }
                      }}
                    />
                  </label>
                  <p className="text-[10px] text-neutral-500">
                    Podés subir una foto desde tu máquina o cambiar la actual.
                  </p>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Alergias o Condiciones Previas</label>
              <input
                type="text"
                value={editingMascota.alergias || ''}
                onChange={e => setEditingMascota({ ...editingMascota, alergias: e.target.value })}
                placeholder="Ej. Reacción a penicilina, intolerancia dietaria..."
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg text-xs"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
              <button
                type="button"
                onClick={() => setIsEditMascotaModalOpen(false)}
                className="px-4 py-2 text-neutral-600 hover:text-neutral-900"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors"
              >
                Guardar Cambios
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* MODAL: AGENDAR TURNO */}
      <Modal
        isOpen={isNewTurnoModalOpen}
        onClose={() => setIsNewTurnoModalOpen(false)}
        title="Agendar Turno Médico"
        subtitle="Validación de no-superposición en agenda médica"
        maxWidth="md"
      >
        <form onSubmit={handleSaveTurno} className="space-y-4 text-xs">
          <div>
            <label className="block text-neutral-600 font-medium mb-1">Paciente *</label>
            <select
              value={newTurnoData.mascotaId}
              onChange={e => setNewTurnoData({ ...newTurnoData, mascotaId: e.target.value })}
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
            <label className="block text-neutral-600 font-medium mb-1">Profesional Veterinario *</label>
            <select
              value={newTurnoData.veterinario}
              onChange={e => setNewTurnoData({ ...newTurnoData, veterinario: e.target.value })}
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            >
              <option value="Dr. Alejandro Morales (M.P. 4812)">Dr. Alejandro Morales (M.P. 4812)</option>
              <option value="Dra. Sofía Carrizo (M.P. 5190)">Dra. Sofía Carrizo (M.P. 5190)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Fecha *</label>
              <input
                type="date"
                required
                value={newTurnoData.fecha}
                onChange={e => setNewTurnoData({ ...newTurnoData, fecha: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Horario *</label>
              <select
                value={newTurnoData.hora}
                onChange={e => setNewTurnoData({ ...newTurnoData, hora: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg font-mono"
              >
                <option value="09:00">09:00 hs</option>
                <option value="09:30">09:30 hs</option>
                <option value="10:00">10:00 hs</option>
                <option value="10:30">10:30 hs</option>
                <option value="11:00">11:00 hs</option>
                <option value="11:30">11:30 hs</option>
                <option value="15:00">15:00 hs</option>
                <option value="15:30">15:30 hs</option>
                <option value="16:00">16:00 hs</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Motivo de la Cita *</label>
            <input
              type="text"
              required
              value={newTurnoData.motivo}
              onChange={e => setNewTurnoData({ ...newTurnoData, motivo: e.target.value })}
              placeholder="Ej. Chequeo preventivo, vacunas, decaimiento..."
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
            <button
              type="button"
              onClick={() => setIsNewTurnoModalOpen(false)}
              className="px-4 py-2 text-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors"
            >
              Confirmar Turno
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: REGISTRAR CONSULTA MÉDICA */}
      <Modal
        isOpen={isNewConsultaModalOpen}
        onClose={() => setIsNewConsultaModalOpen(false)}
        title="Nueva Consulta Médica"
        subtitle="Registro clínico y emisión optativa de derivación de laboratorio"
        maxWidth="lg"
      >
        <form onSubmit={handleSaveConsulta} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Paciente *</label>
              <select
                value={newConsultaData.mascotaId}
                onChange={e => setNewConsultaData({ ...newConsultaData, mascotaId: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              >
                {mascotas.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.nombre} ({m.especie})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Veterinario Actuante</label>
              <input
                type="text"
                value={newConsultaData.veterinario}
                onChange={e => setNewConsultaData({ ...newConsultaData, veterinario: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Turno asociado (opcional)</label>
            <select
              value={newConsultaData.turnoId}
              onChange={e => setNewConsultaData({ ...newConsultaData, turnoId: e.target.value })}
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            >
              <option value="">Consulta sin turno</option>
              {turnos.filter(t => t.mascotaId === newConsultaData.mascotaId && !['Atendido', 'Cancelado', 'Ausente'].includes(t.estado)).map(turno => (
                <option key={turno.id} value={turno.id}>{turno.fecha} {turno.hora} · {turno.veterinario} ({turno.estado})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Motivo de Consulta y Anamnesis *</label>
            <textarea
              required
              rows={2}
              value={newConsultaData.motivo}
              onChange={e => setNewConsultaData({ ...newConsultaData, motivo: e.target.value })}
              placeholder="Descripción de los síntomas o motivo de consulta reportado por el responsable..."
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            />
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Evaluación Clínica / Exploración Física *</label>
            <textarea
              required
              rows={2}
              value={newConsultaData.evaluacionClinica}
              onChange={e => setNewConsultaData({ ...newConsultaData, evaluacionClinica: e.target.value })}
              placeholder="Constantes vitales (T°, FC, FR), mucosas, palpación abdominal, auscultación..."
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Diagnóstico Presuntivo *</label>
              <input
                type="text"
                required
                value={newConsultaData.diagnosticoPresuntivo}
                onChange={e => setNewConsultaData({ ...newConsultaData, diagnosticoPresuntivo: e.target.value })}
                placeholder="Ej. Sospecha de insuficiencia renal / Hemoparásitos..."
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Vacuna Aplicada (Si corresponde)</label>
              <input
                type="text"
                value={newConsultaData.vacunaAplicada}
                onChange={e => setNewConsultaData({ ...newConsultaData, vacunaAplicada: e.target.value })}
                placeholder="Ej. Séxtuple Canina / Antirrábica Lote 904"
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>
          </div>

          <div>
            <label className="block text-neutral-600 font-medium mb-1">Tratamiento e Indicaciones Médicas *</label>
            <textarea
              required
              rows={2}
              value={newConsultaData.tratamiento}
              onChange={e => setNewConsultaData({ ...newConsultaData, tratamiento: e.target.value })}
              placeholder="Medicación prescrita, dosis, reposo, dieta especial..."
              className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
            />
          </div>

          {/* Section: Derivación a Laboratorio */}
          <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#F2E8D8] space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={newConsultaData.requiereAnalisis}
                onChange={e => setNewConsultaData({ ...newConsultaData, requiereAnalisis: e.target.checked })}
                className="w-4 h-4 text-[#2D5864] rounded border-neutral-300 focus:ring-[#2D5864]"
              />
              <span className="font-semibold text-neutral-800">
                ¿Requiere derivación de análisis a Laboratorio Central?
              </span>
            </label>

            {newConsultaData.requiereAnalisis && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div>
                  <label className="block text-neutral-600 font-medium mb-1">Estudio de Laboratorio Solicitado</label>
                  <select
                    value={newConsultaData.tipoAnalisisSolicitado}
                    onChange={e => setNewConsultaData({ ...newConsultaData, tipoAnalisisSolicitado: e.target.value })}
                    className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
                  >
                    <option value="Hemograma Completo">Hemograma Completo</option>
                    <option value="Perfil Bioquímico Hepático">Perfil Bioquímico Hepático</option>
                    <option value="Perfil Renal (Urea y Creatinina)">Perfil Renal (Urea y Creatinina)</option>
                    <option value="Orina Completa y Sedimento">Orina Completa y Sedimento</option>
                    <option value="Coproparasitológico Seriado">Coproparasitológico Seriado</option>
                    <option value="Citología Cutánea / PAAF">Citología Cutánea / PAAF</option>
                  </select>
                </div>
                <div>
                  <label className="block text-neutral-600 font-medium mb-1">Prioridad</label>
                  <select
                    value={newConsultaData.prioridad}
                    onChange={e => setNewConsultaData({ ...newConsultaData, prioridad: e.target.value as any })}
                    className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
                  >
                    <option value="Normal">Normal (24-48 hs)</option>
                    <option value="Urgente">Urgente (Prioridad Máxima)</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
            <button
              type="button"
              onClick={() => setIsNewConsultaModalOpen(false)}
              className="px-4 py-2 text-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors"
            >
              Guardar Consulta
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: HISTORIA CLÍNICA COMPLETA */}
      {selectedMascota && (
        <Modal
          isOpen={isHistoryModalOpen}
          onClose={() => setIsHistoryModalOpen(false)}
          title={`Historia Clínica: ${selectedMascota.nombre}`}
          subtitle={`Especie: ${selectedMascota.especie} · Raza: ${selectedMascota.raza} · ID: ${selectedMascota.id}`}
          maxWidth="xl"
        >
          <div className="space-y-6 text-xs">
            {/* Responsible Header */}
            {(() => {
              const resp = responsables.find(r => r.id === selectedMascota.responsableId);
              return (
                <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#F2E8D8] flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    {selectedMascota.fotoUrl ? (
                      <img
                        src={selectedMascota.fotoUrl}
                        alt={selectedMascota.nombre}
                        className="w-14 h-14 rounded-xl object-cover border border-[#E7E2DA] shadow-xs"
                      />
                    ) : (
                      <div className="w-14 h-14 rounded-xl bg-[#FAF6EF] text-[#2D5864] flex items-center justify-center font-bold text-base shrink-0 border border-[#F2E8D8]">
                        {selectedMascota.nombre.slice(0, 2).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <span className="text-[11px] text-neutral-400 block">Responsable Asignado</span>
                      <span className="font-semibold text-neutral-800">{resp?.nombreCompleto}</span>
                      <span className="text-neutral-500 block text-[11px]">DNI: {resp?.documento} · Tel: {resp?.telefono}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-neutral-400 block">Peso</span>
                    <span className="font-bold text-neutral-900 text-sm tabular-nums">{selectedMascota.pesoKg} kg</span>
                  </div>
                </div>
              );
            })()}

            {/* Previous Consultations */}
            <div>
              <h5 className="font-bold text-neutral-800 uppercase tracking-wider text-[11px] mb-3">
                Registro Histórico de Atenciones Médicas
              </h5>
              {consultas.filter(c => c.mascotaId === selectedMascota.id).length === 0 ? (
                <p className="text-neutral-400 py-3 text-center bg-neutral-50 rounded-lg">
                  No hay consultas médicas registradas aún para este paciente.
                </p>
              ) : (
                <div className="space-y-3">
                  {consultas
                    .filter(c => c.mascotaId === selectedMascota.id)
                    .map(c => (
                      <div key={c.id} className="p-3.5 border border-neutral-200 rounded-lg space-y-2 bg-white">
                        <div className="flex items-center justify-between text-neutral-500 border-b border-neutral-100 pb-2">
                          <span className="font-mono text-neutral-700 font-semibold">{c.fecha} ({c.hora})</span>
                          <span>Atendido por {c.veterinario}</span>
                        </div>
                        <div>
                          <strong className="text-neutral-700">Motivo:</strong> {c.motivo}
                        </div>
                        <div>
                          <strong className="text-neutral-700">Diagnóstico Presuntivo:</strong>{' '}
                          <span className="text-[#2D5864] font-medium">{c.diagnosticoPresuntivo}</span>
                        </div>
                        <div>
                          <strong className="text-neutral-700">Tratamiento:</strong> {c.tratamiento}
                        </div>
                        {c.vacunaAplicada && (
                          <div className="text-[11px] text-emerald-800 bg-emerald-50 p-1.5 rounded">
                            Vacuna aplicada: {c.vacunaAplicada}
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              )}
            </div>

            {/* Analysis & Lab Results History */}
            <div>
              <h5 className="font-bold text-neutral-800 uppercase tracking-wider text-[11px] mb-3">
                Órdenes de Derivación y Resultados Externos
              </h5>
              {ordenes.filter(o => o.mascotaId === selectedMascota.id).length === 0 ? (
                <p className="text-neutral-400 py-3 text-center bg-neutral-50 rounded-lg">
                  No se han solicitado análisis biológicos para este paciente.
                </p>
              ) : (
                <div className="space-y-3">
                  {ordenes
                    .filter(o => o.mascotaId === selectedMascota.id)
                    .map(ord => (
                      <div key={ord.id} className="p-3.5 border border-neutral-200 rounded-lg bg-[#FAF8F5] space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-[#2D5864]">{ord.id}</span>
                          <span className="text-neutral-500 font-mono text-[11px]">{ord.fechaSolicitud}</span>
                        </div>
                        <div className="text-neutral-600">
                          {ord.detalles.map(d => (
                            <div key={d.id} className="flex items-center justify-between py-1 border-t border-neutral-200/50">
                              <span>• {d.tipoAnalisis}</span>
                              <span className="text-[11px] font-mono text-[#5F8E9C] font-semibold">{d.estado}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
