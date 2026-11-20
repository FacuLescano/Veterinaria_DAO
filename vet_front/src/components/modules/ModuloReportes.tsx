import React from 'react';
import { 
  Clock, 
  ShieldAlert, 
  Stethoscope, 
  Microscope 
} from 'lucide-react';
import { useVeterinaria } from '../../context/VeterinariaContext';
import { ReporteTiemposSla } from './reportes/ReporteTiemposSla';
import { ReporteMuestrasRechazadas } from './reportes/ReporteMuestrasRechazadas';
import { ReporteRendimientoClinico } from './reportes/ReporteRendimientoClinico';
import { ReporteEficaciaDiagnostica } from './reportes/ReporteEficaciaDiagnostica';

export const ModuloReportes: React.FC = () => {
  const { activeReportTab, setActiveReportTab } = useVeterinaria();

  return (
    <div className="space-y-6">
      {/* Barra de Selección de Reportes */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl p-2 shadow-xs">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
          {/* Reporte 1 */}
          <button
            onClick={() => setActiveReportTab('reporte1')}
            className={`p-3 text-left rounded-lg transition-all flex items-start gap-3 ${
              activeReportTab === 'reporte1'
                ? 'bg-[#2D5864] text-white shadow-xs'
                : 'hover:bg-neutral-50 text-neutral-700'
            }`}
          >
            <Clock className={`w-5 h-5 shrink-0 mt-0.5 ${activeReportTab === 'reporte1' ? 'text-white' : 'text-[#2D5864]'}`} />
            <div className="min-w-0">
              <span className="font-semibold text-xs leading-tight block">1. Muestras y análisis</span>
              <p className={`text-[11px] mt-0.5 truncate ${activeReportTab === 'reporte1' ? 'text-white/80' : 'text-neutral-500'}`}>
                Extracción y resultados registrados
              </p>
            </div>
          </button>

          {/* Reporte 2 */}
          <button
            onClick={() => setActiveReportTab('reporte2')}
            className={`p-3 text-left rounded-lg transition-all flex items-start gap-3 ${
              activeReportTab === 'reporte2'
                ? 'bg-[#2D5864] text-white shadow-xs'
                : 'hover:bg-neutral-50 text-neutral-700'
            }`}
          >
            <ShieldAlert className={`w-5 h-5 shrink-0 mt-0.5 ${activeReportTab === 'reporte2' ? 'text-white' : 'text-[#5F8E9C]'}`} />
            <div className="min-w-0">
              <span className="font-semibold text-xs leading-tight block">2. Recepción en laboratorio</span>
              <p className={`text-[11px] mt-0.5 truncate ${activeReportTab === 'reporte2' ? 'text-white/80' : 'text-neutral-500'}`}>
                Estados y tiempos de recepción
              </p>
            </div>
          </button>

          {/* Reporte 3 */}
          <button
            onClick={() => setActiveReportTab('reporte3')}
            className={`p-3 text-left rounded-lg transition-all flex items-start gap-3 ${
              activeReportTab === 'reporte3'
                ? 'bg-[#2D5864] text-white shadow-xs'
                : 'hover:bg-neutral-50 text-neutral-700'
            }`}
          >
            <Stethoscope className={`w-5 h-5 shrink-0 mt-0.5 ${activeReportTab === 'reporte3' ? 'text-white' : 'text-[#5F8E9C]'}`} />
            <div className="min-w-0">
              <span className="font-semibold text-xs leading-tight block">3. Actividad médica</span>
              <p className={`text-[11px] mt-0.5 truncate ${activeReportTab === 'reporte3' ? 'text-white/80' : 'text-neutral-500'}`}>
                Turnos, consultas y órdenes
              </p>
            </div>
          </button>

          {/* Reporte 4 */}
          <button
            onClick={() => setActiveReportTab('reporte4')}
            className={`p-3 text-left rounded-lg transition-all flex items-start gap-3 ${
              activeReportTab === 'reporte4'
                ? 'bg-[#2D5864] text-white shadow-xs'
                : 'hover:bg-neutral-50 text-neutral-700'
            }`}
          >
            <Microscope className={`w-5 h-5 shrink-0 mt-0.5 ${activeReportTab === 'reporte4' ? 'text-white' : 'text-[#5F8E9C]'}`} />
            <div className="min-w-0">
              <span className="font-semibold text-xs leading-tight block">4. Resultados de laboratorio</span>
              <p className={`text-[11px] mt-0.5 truncate ${activeReportTab === 'reporte4' ? 'text-white/80' : 'text-neutral-500'}`}>
                Resultados recibidos y pendientes
              </p>
            </div>
          </button>
        </div>
      </div>

      {activeReportTab === 'reporte1' && <ReporteTiemposSla />}
      
      {activeReportTab === 'reporte2' && <ReporteMuestrasRechazadas />}

      {activeReportTab === 'reporte3' && <ReporteRendimientoClinico />}

      {activeReportTab === 'reporte4' && <ReporteEficaciaDiagnostica />}
    </div>
  );
};
