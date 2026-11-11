import React from 'react';
import { RemitoBiologico, MuestraBiologica, Mascota } from '../../types/veterinaria';
import { Modal } from './Modal';
import { Printer, ShieldCheck, Thermometer, Clock } from 'lucide-react';

interface RemitoPrintModalProps {
  isOpen: boolean;
  onClose: () => void;
  remito: RemitoBiologico;
  muestras: MuestraBiologica[];
  mascotas: Mascota[];
}

export const RemitoPrintModal: React.FC<RemitoPrintModalProps> = ({
  isOpen,
  onClose,
  remito,
  muestras,
  mascotas
}) => {
  const remitoMuestras = muestras.filter(m => remito.muestrasIds.includes(m.id));

  const handlePrint = () => {
    window.print();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Remito Biológico Oficial — ${remito.id}`}
      subtitle="Documento de cadena de custodia y derivación sanitaria"
      maxWidth="xl"
    >
      <div className="space-y-6">
        {/* Printable Sheet */}
        <div
          id="remito-sticker-printable"
          className="border-2 border-dashed border-neutral-300 rounded-xl p-5 bg-white text-neutral-800 text-xs space-y-4 print:border-2 print:border-black print:p-4 print:m-0 print:rounded-none"
        >
          {/* Sticker Banner for package labeling */}
          <div className="flex items-center justify-between bg-neutral-100 print:bg-neutral-200 px-3 py-1.5 rounded text-[10px] font-mono uppercase tracking-wider text-neutral-700 border border-neutral-200">
            <span>🏷️ Rótulo Oficial de Adhesión para Embalaje</span>
            <span className="font-bold text-[#2D5864] print:text-black">Precinto #{remito.precintoCodigo}</span>
          </div>

          {/* Header */}
          <div className="flex items-start justify-between border-b border-neutral-200 pb-3">
            <div className="flex items-center gap-3">
              <img
                src="/assets/aistudio/Gemini_Generated_Image_o95dgio95dgio95d-removebg-preview_cbe90b76.png"
                alt="Patitas & Co. Logo"
                className="w-11 h-11 object-contain"
              />
              <div>
                <h4 className="font-bold text-[#2D5864] text-base leading-tight">PATITAS & CO.</h4>
                <p className="text-xs text-neutral-500">Red de Clínicas Veterinarias & Derivación</p>
                <p className="text-[10px] text-neutral-400">Córdoba, Argentina · Res. SENASA N° 412/2026</p>
              </div>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-mono font-semibold uppercase text-[#5F8E9C] tracking-wider block">
                REMITO BIOLÓGICO
              </span>
              <span className="font-mono text-base font-bold text-neutral-900 block">
                {remito.id}
              </span>
              <span className="text-[11px] text-neutral-500 block mt-0.5">
                Emisión: {remito.fechaEmision}
              </span>
            </div>
          </div>

          {/* Logistics Data Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3.5 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] text-xs">
            <div>
              <span className="text-neutral-500 font-medium block">Origen (Clínica Solicitante):</span>
              <span className="font-semibold text-neutral-800">{remito.clinicaOrigen}</span>
              <span className="text-neutral-500 font-medium block mt-2">Destino (Laboratorio Central):</span>
              <span className="font-semibold text-neutral-800">{remito.laboratorioDestino}</span>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-neutral-500 font-medium">Contenedor Isotérmico:</span>
                <span className="font-mono font-semibold text-neutral-800">{remito.conservadoraId}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neutral-500 font-medium flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#2D5864]" />
                  Precinto Sanitario:
                </span>
                <span className="font-mono font-bold text-[#2D5864]">{remito.precintoCodigo}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neutral-500 font-medium flex items-center gap-1">
                  <Thermometer className="w-3.5 h-3.5 text-[#5F8E9C]" />
                  T° de Despacho:
                </span>
                <span className="font-mono font-semibold text-neutral-800">{remito.temperaturaDespachoC}°C</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neutral-500 font-medium flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-neutral-400" />
                  Transportista:
                </span>
                <span className="font-medium text-neutral-800">{remito.transportista}</span>
              </div>
            </div>
          </div>

          {/* Muestras Table */}
          <div>
            <h5 className="text-xs font-semibold uppercase tracking-wider text-neutral-600 mb-2">
              Detalle de Muestras Biológicas Despachadas ({remitoMuestras.length})
            </h5>
            <div className="overflow-x-auto border border-neutral-200 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-neutral-50 text-neutral-600 border-b border-neutral-200">
                  <tr>
                    <th className="py-2 px-3 font-semibold">ID Muestra</th>
                    <th className="py-2 px-3 font-semibold">Rótulo Tubo</th>
                    <th className="py-2 px-3 font-semibold">Paciente</th>
                    <th className="py-2 px-3 font-semibold">Material</th>
                    <th className="py-2 px-3 font-semibold">Conservación</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {remitoMuestras.map(m => {
                    const mascota = mascotas.find(pet => pet.id === 'MASC-001'); // fallback / match
                    return (
                      <tr key={m.id} className="hover:bg-neutral-50/50">
                        <td className="py-2 px-3 font-mono font-semibold text-[#2D5864]">{m.id}</td>
                        <td className="py-2 px-3 font-mono text-neutral-700">{m.identificacionFisica}</td>
                        <td className="py-2 px-3 text-neutral-800 font-medium">{mascota?.nombre || 'Paciente'}</td>
                        <td className="py-2 px-3 text-neutral-600">{m.tipoMaterial}</td>
                        <td className="py-2 px-3 text-neutral-600">{m.condicionConservacion}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Signatures & Custody Notice */}
          <div className="pt-4 border-t border-neutral-200 grid grid-cols-2 gap-8 text-xs text-neutral-500">
            <div className="border-t border-dashed border-neutral-400 pt-2 text-center mt-6">
              <p className="font-semibold text-neutral-800">{remito.responsableDespacho}</p>
              <p className="text-[11px]">Responsable de Embalaje & Despacho</p>
              <p className="text-[10px] text-neutral-400">Patitas & Co. Clínica</p>
            </div>
            <div className="border-t border-dashed border-neutral-400 pt-2 text-center mt-6">
              <p className="font-semibold text-neutral-800">{remito.transportista}</p>
              <p className="text-[11px]">Transportista / Custodia Biológica</p>
              <p className="text-[10px] text-neutral-400">Firma y Sello de Salida</p>
            </div>
          </div>

          <div className="text-[11px] text-neutral-500 bg-amber-50/70 p-2.5 rounded border border-amber-200/60 leading-relaxed">
            <strong>Declaración de Bioseguridad:</strong> Este envío contiene material biológico clasificado. El laboratorio receptor debe inspeccionar y verificar la integridad del precinto sanitario #{remito.precintoCodigo}. Si el precinto se encuentra violado o roto, las muestras quedan automáticamente rechazadas.
          </div>
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-end gap-3 pt-2 print:hidden no-print">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-neutral-600 hover:text-neutral-900 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors"
          >
            Cerrar
          </button>
          <button
            type="button"
            onClick={handlePrint}
            className="px-4 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-2 shadow-xs"
          >
            <Printer className="w-4 h-4" />
            Imprimir Remito
          </button>
        </div>
      </div>
    </Modal>
  );
};
