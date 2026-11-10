import React, { useState } from 'react';
import { useVeterinaria } from '../../context/VeterinariaContext';
import { RemitoBiologico, MuestraBiologica } from '../../types/veterinaria';
import { Modal } from '../common/Modal';
import { RemitoPrintModal } from '../common/RemitoPrintModal';
import { 
  Truck, 
  Package, 
  ShieldCheck, 
  FileText, 
  Plus, 
  Printer, 
  Thermometer, 
  CheckCircle2, 
  Clock, 
  AlertTriangle 
} from 'lucide-react';

export const Modulo3PreparacionDespacho: React.FC = () => {
  const {
    conservadoras,
    muestras,
    remitos,
    precintos,
    mascotas,
    prepararEnvio
  } = useVeterinaria();

  const [isNewDespachoModalOpen, setIsNewDespachoModalOpen] = useState(false);
  const [selectedRemitoForPrint, setSelectedRemitoForPrint] = useState<RemitoBiologico | null>(null);

  // Form State for Dispatch Preparation
  const [formData, setFormData] = useState({
    conservadoraId: conservadoras.find(c => c.disponible)?.id || conservadoras[0]?.id || '',
    precintoCodigo: `PREC-${Math.floor(10000 + Math.random() * 90000)}`,
    responsableDespacho: 'Enf. Juan Méndez',
    transportista: 'Transportes BioLog (Roberto Gómez)',
    selectedMuestrasIds: [] as string[],
    temperaturaDespachoC: 4.5,
    observaciones: 'Cadena de frío mantenida con geles eutécticos congelados.'
  });

  // Muestras that are ready to be packed (Extraída state)
  const muestrasListasParaEmpacar = muestras.filter(m => m.estadoActual === 'Extraída');

  const handleToggleMuestra = (id: string) => {
    setFormData(prev => ({
      ...prev,
      selectedMuestrasIds: prev.selectedMuestrasIds.includes(id)
        ? prev.selectedMuestrasIds.filter(mId => mId !== id)
        : [...prev.selectedMuestrasIds, id]
    }));
  };

  const handleCreateDespacho = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.selectedMuestrasIds.length === 0) return;

    const nuevoRemito = prepararEnvio({
      conservadoraId: formData.conservadoraId,
      precintoCodigo: formData.precintoCodigo,
      responsableDespacho: formData.responsableDespacho,
      transportista: formData.transportista,
      muestrasIds: formData.selectedMuestrasIds,
      temperaturaDespachoC: Number(formData.temperaturaDespachoC),
      observaciones: formData.observaciones
    });

    setIsNewDespachoModalOpen(false);
    // Open printable remito view immediately for convenience
    setSelectedRemitoForPrint(nuevoRemito);
  };

  return (
    <>
      {/* Main Module Content - Hidden when printing so only the remito label prints */}
      <div className="space-y-6 print:hidden">
        {/* Top Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E7E2DA] pb-4">
        <div>
          <h3 className="text-sm font-bold text-neutral-900">
            Envíos y Remitos de Derivación
          </h3>
          <p className="text-xs text-neutral-500 mt-0.5">
            Empaquetado en conservadoras isotérmicas, colocación de precinto sanitario y custodia biológica
          </p>
        </div>

        <button
          onClick={() => {
            // Pre-select all ready samples by default
            setFormData(prev => ({
              ...prev,
              precintoCodigo: `PREC-${Math.floor(10000 + Math.random() * 90000)}`,
              selectedMuestrasIds: muestrasListasParaEmpacar.map(m => m.id)
            }));
            setIsNewDespachoModalOpen(true);
          }}
          className="px-3.5 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs whitespace-nowrap self-start sm:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Preparar y Despachar Envío</span>
        </button>
      </div>

      {/* Conservadoras & Muestras Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {conservadoras.map(c => (
          <div
            key={c.id}
            className="p-4 bg-white border border-[#E7E2DA] rounded-xl shadow-xs space-y-2 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-[#2D5864]">{c.id}</span>
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    c.disponible ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                  }`}
                >
                  {c.disponible ? 'Disponible' : 'En tránsito / Ocupada'}
                </span>
              </div>
              <h4 className="font-semibold text-sm text-neutral-800 mt-1">{c.nombre}</h4>
              <p className="text-xs text-neutral-500">{c.temperaturaRequerida}</p>
            </div>
            <div className="text-[11px] text-neutral-400 pt-2 border-t border-neutral-100 flex items-center justify-between">
              <span>Capacidad: {c.capacidadMuestras} tubos</span>
              <Package className="w-4 h-4 text-[#8C8C91]" />
            </div>
          </div>
        ))}
      </div>

      {/* Remitos List */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl overflow-hidden shadow-xs">
        <div className="p-4 border-b border-[#F2E8D8] flex items-center justify-between bg-[#FAF8F5]">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#2D5864]">
              Historial de Remitos Biológicos Despachados
            </h4>
            <p className="text-[11px] text-neutral-500">
              Documentos de derivación oficial con detalle de muestras y precinto
            </p>
          </div>
          <span className="text-xs font-mono text-neutral-600 bg-white px-2 py-1 rounded border border-neutral-200">
            {remitos.length} remitos emitidos
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-neutral-50 text-neutral-500 border-b border-neutral-200">
              <tr>
                <th className="py-2.5 px-4 font-semibold">N° Remito</th>
                <th className="py-2.5 px-4 font-semibold">Fecha Despacho</th>
                <th className="py-2.5 px-4 font-semibold">Conservadora & Precinto</th>
                <th className="py-2.5 px-4 font-semibold">Muestras</th>
                <th className="py-2.5 px-4 font-semibold">Transportista</th>
                <th className="py-2.5 px-4 font-semibold">T° Salida</th>
                <th className="py-2.5 px-4 font-semibold">Estado Envio</th>
                <th className="py-2.5 px-4 font-semibold text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {remitos.map(r => {
                return (
                  <tr key={r.id} className="hover:bg-neutral-50/70 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-[#2D5864] whitespace-nowrap">
                      {r.id}
                    </td>
                    <td className="py-3 px-4 font-mono text-neutral-600 whitespace-nowrap">
                      {r.fechaEmision}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-neutral-800 block">{r.conservadoraId}</span>
                      <span className="font-mono text-[11px] text-[#2D5864] flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3 text-[#2D5864]" />
                        {r.precintoCodigo}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-neutral-800">{r.muestrasIds.length} muestras</span>
                      <span className="block text-[11px] text-neutral-400 font-mono">
                        {r.muestrasIds.join(', ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-neutral-700">
                      {r.transportista}
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold text-neutral-800 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1">
                        <Thermometer className="w-3 h-3 text-[#5F8E9C]" />
                        {r.temperaturaDespachoC}°C
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex text-[11px] font-medium px-2 py-0.5 rounded-md ${
                          r.estado === 'Recibido'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                            : r.estado === 'Con incidencias'
                            ? 'bg-rose-100 text-rose-800 border border-rose-200 font-semibold'
                            : 'bg-amber-100 text-amber-800 border border-amber-200'
                        }`}
                      >
                        {r.estado}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => setSelectedRemitoForPrint(r)}
                        className="px-2.5 py-1 text-xs font-semibold text-[#2D5864] hover:bg-[#FAF6EF] border border-[#2D5864]/20 rounded-md transition-colors inline-flex items-center gap-1"
                      >
                        <Printer className="w-3.5 h-3.5" />
                        <span>Ver Remito</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL: PREPARAR Y DESPACHAR ENVÍO */}
      <Modal
        isOpen={isNewDespachoModalOpen}
        onClose={() => setIsNewDespachoModalOpen(false)}
        title="Preparar y Despachar Envío a Laboratorio"
        subtitle="Agrupar muestras en conservadora, asignar precinto sanitario y emitir remito"
        maxWidth="lg"
      >
        <form onSubmit={handleCreateDespacho} className="space-y-4 text-xs">
          {/* Muestras Selection */}
          <div className="space-y-2">
            <span className="font-bold text-[#2D5864] uppercase tracking-wider text-[11px] block">
              1. Seleccionar Muestras a Empacar en este Envío *
            </span>

            {muestrasListasParaEmpacar.length === 0 ? (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs">
                No hay muestras en estado &ldquo;Extraída&rdquo; pendientes de despacho. Puedes generar una nueva muestra desde el Módulo 2 o incluir muestras existentes.
              </div>
            ) : (
              <div className="max-h-40 overflow-y-auto border border-[#E7E2DA] rounded-lg divide-y divide-neutral-100">
                {muestrasListasParaEmpacar.map(m => {
                  const isChecked = formData.selectedMuestrasIds.includes(m.id);
                  return (
                    <label
                      key={m.id}
                      className={`flex items-center justify-between p-2.5 cursor-pointer transition-colors ${
                        isChecked ? 'bg-[#FAF6EF]' : 'hover:bg-neutral-50'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleMuestra(m.id)}
                          className="w-4 h-4 text-[#2D5864] rounded border-neutral-300 focus:ring-[#2D5864]"
                        />
                        <div>
                          <span className="font-mono font-bold text-[#2D5864] mr-2">{m.id}</span>
                          <span className="text-neutral-800 font-medium">{m.tipoMaterial}</span>
                          <span className="block text-[11px] text-neutral-400">Rótulo: {m.identificacionFisica}</span>
                        </div>
                      </div>
                      <span className="text-[11px] text-neutral-500 font-mono">
                        {m.condicionConservacion}
                      </span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>

          {/* Cooler & Seal */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">
                Conservadora Isotérmica *
              </label>
              <select
                value={formData.conservadoraId}
                onChange={e => setFormData({ ...formData, conservadoraId: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              >
                {conservadoras.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.id} - {c.nombre} ({c.disponible ? 'Disponible' : 'En uso'})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">
                Código Único de Precinto Sanitario *
              </label>
              <input
                type="text"
                required
                value={formData.precintoCodigo}
                onChange={e => setFormData({ ...formData, precintoCodigo: e.target.value })}
                placeholder="PREC-XXXXX"
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg font-mono font-bold text-[#2D5864]"
              />
              <span className="text-[10px] text-neutral-400 mt-0.5 block">
                Este precinto será inspeccionado por el laboratorio de destino.
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">Responsable de Despacho *</label>
              <input
                type="text"
                required
                value={formData.responsableDespacho}
                onChange={e => setFormData({ ...formData, responsableDespacho: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Transportista / Chofer *</label>
              <input
                type="text"
                required
                value={formData.transportista}
                onChange={e => setFormData({ ...formData, transportista: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-neutral-600 font-medium mb-1">
                Temperatura Medida al Despacho (°C) *
              </label>
              <input
                type="number"
                step="0.1"
                required
                value={formData.temperaturaDespachoC}
                onChange={e => setFormData({ ...formData, temperaturaDespachoC: parseFloat(e.target.value) || 0 })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg font-mono"
              />
            </div>

            <div>
              <label className="block text-neutral-600 font-medium mb-1">Observaciones</label>
              <input
                type="text"
                value={formData.observaciones}
                onChange={e => setFormData({ ...formData, observaciones: e.target.value })}
                className="w-full p-2 bg-white border border-[#E7E2DA] rounded-lg"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-100">
            <button
              type="button"
              onClick={() => setIsNewDespachoModalOpen(false)}
              className="px-4 py-2 text-neutral-600"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={formData.selectedMuestrasIds.length === 0}
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors disabled:opacity-50"
            >
              Emitir Remito y Despachar ({formData.selectedMuestrasIds.length} muestras)
            </button>
          </div>
        </form>
      </Modal>
      </div>

      {/* MODAL: PRINT PREVIEW */}
      {selectedRemitoForPrint && (
        <RemitoPrintModal
          isOpen={!!selectedRemitoForPrint}
          onClose={() => setSelectedRemitoForPrint(null)}
          remito={selectedRemitoForPrint}
          muestras={muestras}
          mascotas={mascotas}
        />
      )}
    </>
  );
};
