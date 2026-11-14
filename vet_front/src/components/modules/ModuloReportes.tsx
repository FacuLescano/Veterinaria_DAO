import React, { useState } from 'react';
import { 
  Clock, 
  ShieldAlert, 
  Stethoscope, 
  Microscope 
} from 'lucide-react';

import { ReporteTiemposSla } from './reportes/ReporteTiemposSla';
import { ReporteMuestrasRechazadas } from './reportes/ReporteMuestrasRechazadas';
import { ReportePlaceholder } from './reportes/ReportePlaceholder';

export const ModuloReportes: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'reporte1' | 'reporte2' | 'reporte3' | 'reporte4'>('reporte1');

  return (
    <div className="space-y-6">
      {/* Barra de Selección de Reportes */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl p-2 shadow-xs">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
          {/* Reporte 1 */}
          <button
            onClick={() => setActiveTab('reporte1')}
            className={`p-3 text-left rounded-lg transition-all flex items-start gap-3 ${
              activeTab === 'reporte1'
                ? 'bg-[#2D5864] text-white shadow-xs'
                : 'hover:bg-neutral-50 text-neutral-700'
            }`}
          >
            <Clock className={`w-5 h-5 shrink-0 mt-0.5 ${activeTab === 'reporte1' ? 'text-white' : 'text-[#2D5864]'}`} />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-xs leading-tight">1. Tránsito & SLA</span>
                <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                  activeTab === 'reporte1' ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-800'
                }`}>
                  Activo
                </span>
              </div>
              <p className={`text-[11px] mt-0.5 truncate ${activeTab === 'reporte1' ? 'text-white/80' : 'text-neutral-500'}`}>
                Tiempos de viaje, proceso y cumplimiento
              </p>
            </div>
          </button>

          {/* Reporte 2 */}
          <button
            onClick={() => setActiveTab('reporte2')}
            className={`p-3 text-left rounded-lg transition-all flex items-start gap-3 ${
              activeTab === 'reporte2'
                ? 'bg-[#2D5864] text-white shadow-xs'
                : 'hover:bg-neutral-50 text-neutral-700'
            }`}
          >
            <ShieldAlert className={`w-5 h-5 shrink-0 mt-0.5 ${activeTab === 'reporte2' ? 'text-white' : 'text-[#5F8E9C]'}`} />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-xs leading-tight">2. Muestras Rechazadas</span>
                <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                  activeTab === 'reporte2' ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-800'
                }`}>
                  Activo
                </span>
              </div>
              <p className={`text-[11px] mt-0.5 truncate ${activeTab === 'reporte2' ? 'text-white/80' : 'text-neutral-500'}`}>
                Bioseguridad, precintos y cadena de frío
              </p>
            </div>
          </button>

          {/* Reporte 3 */}
          <button
            onClick={() => setActiveTab('reporte3')}
            className={`p-3 text-left rounded-lg transition-all flex items-start gap-3 ${
              activeTab === 'reporte3'
                ? 'bg-[#2D5864] text-white shadow-xs'
                : 'hover:bg-neutral-50 text-neutral-700'
            }`}
          >
            <Stethoscope className={`w-5 h-5 shrink-0 mt-0.5 ${activeTab === 'reporte3' ? 'text-white' : 'text-[#5F8E9C]'}`} />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-xs leading-tight">3. Rendimiento Médico</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded-full font-bold bg-amber-100 text-amber-800">
                  Próximo
                </span>
              </div>
              <p className={`text-[11px] mt-0.5 truncate ${activeTab === 'reporte3' ? 'text-white/80' : 'text-neutral-500'}`}>
                Consultas, derivaciones y ausentismo
              </p>
            </div>
          </button>

          {/* Reporte 4 */}
          <button
            onClick={() => setActiveTab('reporte4')}
            className={`p-3 text-left rounded-lg transition-all flex items-start gap-3 ${
              activeTab === 'reporte4'
                ? 'bg-[#2D5864] text-white shadow-xs'
                : 'hover:bg-neutral-50 text-neutral-700'
            }`}
          >
            <Microscope className={`w-5 h-5 shrink-0 mt-0.5 ${activeTab === 'reporte4' ? 'text-white' : 'text-[#5F8E9C]'}`} />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-xs leading-tight">4. Eficacia Diagnóstica</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded-full font-bold bg-amber-100 text-amber-800">
                  Próximo
                </span>
              </div>
              <p className={`text-[11px] mt-0.5 truncate ${activeTab === 'reporte4' ? 'text-white/80' : 'text-neutral-500'}`}>
                Hallazgos críticos y positividad por especie
              </p>
            </div>
          </button>
        </div>
      </div>

      {activeTab === 'reporte1' && <ReporteTiemposSla />}
      
      {activeTab === 'reporte2' && <ReporteMuestrasRechazadas />}

      {activeTab === 'reporte3' && (
        <ReportePlaceholder
          titulo="Reporte 3: Rendimiento Clínico y Derivaciones"
          descripcion="Productividad de los profesionales veterinarios, tasa de derivación a estudios de laboratorio vs tratamientos ambulatorios y control de ausentismo en turnos agendados."
          icono={Stethoscope}
          badge="Etapa siguiente · Estructura de modelo y datos ya preparada"
          colorScheme="blue"
        />
      )}

      {activeTab === 'reporte4' && (
        <ReportePlaceholder
          titulo="Reporte 4: Eficacia Diagnóstica & Hallazgos Críticos"
          descripcion="Porcentaje de análisis que arrojaron valores patológicos o fuera de rango de referencia, cruzados con la especie del animal y grupo etario para epidemiología veterinaria."
          icono={Microscope}
          badge="Etapa siguiente · Estructura de modelo y datos ya preparada"
          colorScheme="emerald"
        />
      )}
    </div>
  );
};
