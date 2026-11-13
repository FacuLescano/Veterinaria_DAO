import React, { useEffect, useState } from 'react';
import { useVeterinaria } from '../context/VeterinariaContext';
import { Menu, RotateCcw, ShieldCheck, Plus } from 'lucide-react';

interface HeaderProps {
  onOpenQuickNew?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenQuickNew }) => {
  const [apiDisponible, setApiDisponible] = useState<boolean | null>(null);
  const {
    activeModule,
    setIsMobileMenuOpen,
    reloadFromDatabase,
    mascotas,
    muestras,
    ordenes
  } = useVeterinaria();

  useEffect(() => {
    let activo = true;
    const comprobarApi = async () => {
      try {
        const response = await fetch('/health');
        if (activo) setApiDisponible(response.ok);
      } catch {
        if (activo) setApiDisponible(false);
      }
    };
    void comprobarApi();
    const interval = window.setInterval(comprobarApi, 15000);
    return () => {
      activo = false;
      window.clearInterval(interval);
    };
  }, []);

  const moduleTitles: Record<string, { title: string; subtitle: string }> = {
    pacientes: {
      title: 'Módulo 1: Pacientes y Atención Clínica',
      subtitle: 'Clientes, mascotas, agenda médica e historia clínica'
    },
    ordenes: {
      title: 'Módulo 2: Órdenes y Muestras Biológicas',
      subtitle: 'Solicitudes de laboratorio, identificación de tubos y trazabilidad'
    },
    despacho: {
      title: 'Módulo 3: Preparación, Remito y Despacho',
      subtitle: 'Contenedores isotérmicos, precinto sanitario y custodia en transporte'
    },
    recepcion: {
      title: 'Módulo 4: Recepción, Precintos y Resultados',
      subtitle: 'Verificación de integridad, gestión de incidencias e informes'
    },
    notificaciones: {
      title: 'Bandeja general de notificaciones',
      subtitle: 'Recepción de muestras y novedades de laboratorio'
    },
    python: {
      title: 'Código Python & GUI Tkinter (Cátedra)',
      subtitle: 'Implementación POO y formularios según material conceptual 2026'
    }
  };

  const current = moduleTitles[activeModule] || {
    title: 'Patitas & Co.',
    subtitle: 'Sistema Veterinario'
  };

  return (
    <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-xs border-b border-[#E7E2DA] px-4 md:px-8 py-3.5 flex items-center justify-between gap-4 transition-all">
      {/* Left: Mobile hamburger + Breadcrumb */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={() => setIsMobileMenuOpen(true)}
          className="md:hidden p-2 text-neutral-600 hover:text-[#2D5864] hover:bg-[#FAF8F5] rounded-lg transition-colors"
          aria-label="Abrir menú de navegación"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs text-[#8C8C91]">
            <span className="font-medium text-[#2D5864]">Patitas & Co.</span>
          </div>
          <h1 className="text-sm md:text-base font-bold text-neutral-900 tracking-tight truncate mt-0.5">
            {current.title.split(':')[1]?.trim() || current.title}
          </h1>
        </div>
      </div>

      {/* Right Actions: Quick stats pill-free, Reset, Primary Action */}
      <div className="flex items-center gap-2.5 shrink-0">
        <span
          role="status"
          title={apiDisponible === null ? 'Comprobando la API' : apiDisponible ? 'API disponible; pacientes y responsables se guardan en SQLite' : 'No se pudo conectar con el backend'}
          className={`hidden md:inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${apiDisponible ? 'bg-emerald-50 text-emerald-700' : apiDisponible === false ? 'bg-rose-50 text-rose-700' : 'bg-neutral-100 text-neutral-500'}`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${apiDisponible ? 'bg-emerald-500' : apiDisponible === false ? 'bg-rose-500' : 'bg-neutral-400'}`} />
          {apiDisponible === null ? 'API…' : apiDisponible ? 'API disponible' : 'API sin conexión'}
        </span>
        {/* Subtle quick counters (unboxed text) */}
        <div className="hidden lg:flex items-center gap-3 text-xs text-neutral-500 mr-2 border-r border-neutral-200 pr-4">
          <span>
            <strong className="font-semibold text-neutral-800 tabular-nums">{mascotas.length}</strong> pacientes
          </span>
          <span aria-hidden="true">·</span>
          <span>
            <strong className="font-semibold text-neutral-800 tabular-nums">{ordenes.length}</strong> órdenes
          </span>
          <span aria-hidden="true">·</span>
          <span>
            <strong className="font-semibold text-neutral-800 tabular-nums">{muestras.length}</strong> muestras
          </span>
        </div>

        {/* Reset Demo Data Button */}
        <button
          onClick={reloadFromDatabase}
          title="Volver a cargar los datos guardados en SQLite"
          className="p-2 text-xs font-medium text-neutral-600 hover:text-neutral-900 hover:bg-[#FAF6EF] border border-[#E7E2DA] rounded-lg transition-colors flex items-center gap-1.5"
          aria-label="Recargar datos guardados"
        >
          <RotateCcw className="w-3.5 h-3.5 text-[#8C8C91]" />
          <span className="hidden sm:inline">Recargar datos</span>
        </button>

        {/* Primary Action Button (triggers contextual modal/form) */}
        {onOpenQuickNew && activeModule !== 'python' && (
          <button
            onClick={onOpenQuickNew}
            className="px-3.5 py-2 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">
              {activeModule === 'pacientes' && 'Nueva Atención / Paciente'}
              {activeModule === 'ordenes' && 'Nueva Orden / Muestra'}
              {activeModule === 'despacho' && 'Nuevo Remito de Envío'}
              {activeModule === 'recepcion' && 'Verificar Precinto'}
            </span>
            <span className="sm:hidden">Nuevo</span>
          </button>
        )}
      </div>
    </header>
  );
};
