import React from 'react';
import { useVeterinaria, ActiveModule } from '../context/VeterinariaContext';
import { 
  Users, 
  FlaskConical, 
  Truck, 
  ClipboardCheck, 
  Code2, 
  PanelLeftClose, 
  PanelLeftOpen, 
  X,
  AlertTriangle
} from 'lucide-react';

interface NavItem {
  id: ActiveModule;
  label: string;
  shortLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  badgeCount?: number;
  badgeAlert?: boolean;
}

export const Sidebar: React.FC = () => {
  const {
    activeModule,
    setActiveModule,
    isSidebarCollapsed,
    setIsSidebarCollapsed,
    isMobileMenuOpen,
    setIsMobileMenuOpen,
    remitos,
    incidencias,
    ordenes
  } = useVeterinaria();

  // Pending shipments to receive
  const enviosEnTransito = remitos.filter(r => r.estado === 'Despachado').length;
  // Incidents unresolved
  const incidenciasActivas = incidencias.filter(i => !i.resuelto).length;
  // Orders pending
  const ordenesPendientes = ordenes.filter(o => o.estado !== 'Con resultados' && o.estado !== 'Cancelada').length;

  const navItems: NavItem[] = [
    {
      id: 'pacientes',
      label: 'Pacientes y Atención',
      shortLabel: 'Atención',
      icon: Users
    },
    {
      id: 'ordenes',
      label: 'Órdenes y Muestras',
      shortLabel: 'Muestras',
      icon: FlaskConical,
      badgeCount: ordenesPendientes > 0 ? ordenesPendientes : undefined
    },
    {
      id: 'despacho',
      label: 'Preparación y Despacho',
      shortLabel: 'Despacho',
      icon: Truck,
      badgeCount: enviosEnTransito > 0 ? enviosEnTransito : undefined
    },
    {
      id: 'recepcion',
      label: 'Recepción y Resultados',
      shortLabel: 'Recepción',
      icon: ClipboardCheck,
      badgeCount: incidenciasActivas > 0 ? incidenciasActivas : undefined,
      badgeAlert: incidenciasActivas > 0
    }
  ];

  const handleSelectModule = (id: ActiveModule) => {
    setActiveModule(id);
    if (isMobileMenuOpen) {
      setIsMobileMenuOpen(false);
    }
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white border-r border-[#E7E2DA]">
      {/* Brand Header */}
      <div className={`p-4 border-b border-[#F2E8D8] flex items-center justify-between transition-all ${isSidebarCollapsed ? 'px-2 justify-center' : 'px-4'}`}>
        <div className="flex items-center gap-3 overflow-hidden">
          <img
            src="/assets/aistudio/Gemini_Generated_Image_o95dgio95dgio95d-removebg-preview_cbe90b76.png"
            alt="Patitas & Co. Logo"
            className="w-10 h-10 object-contain shrink-0"
          />
          {!isSidebarCollapsed && (
            <div className="min-w-0">
              <span className="font-bold text-sm tracking-tight text-[#2D5864] block truncate">
                Patitas & Co.
              </span>
              <span className="text-[11px] text-[#8C8C91] block truncate">
                Red Veterinaria & Lab
              </span>
            </div>
          )}
        </div>

        {/* Mobile Close Button */}
        <button
          onClick={() => setIsMobileMenuOpen(false)}
          className="md:hidden text-[#8C8C91] hover:text-[#2D5864] p-1 rounded-md"
          aria-label="Cerrar menú móvil"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Desktop Collapse Toggle */}
        <button
          onClick={() => setIsSidebarCollapsed(prev => !prev)}
          className={`hidden md:flex text-[#8C8C91] hover:text-[#2D5864] p-1.5 rounded-lg hover:bg-[#FAF8F5] transition-colors ${isSidebarCollapsed ? 'mt-2' : ''}`}
          aria-label={isSidebarCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral"}
          title={isSidebarCollapsed ? "Expandir menú" : "Colapsar menú"}
        >
          {isSidebarCollapsed ? (
            <PanelLeftOpen className="w-4 h-4" />
          ) : (
            <PanelLeftClose className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-2.5 space-y-1 overflow-y-auto" aria-label="Navegación principal de módulos">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = activeModule === item.id;

          return (
            <button
              key={item.id}
              onClick={() => handleSelectModule(item.id)}
              title={item.label}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all group relative ${
                isActive
                  ? 'bg-[#2D5864] text-white shadow-xs'
                  : 'text-neutral-600 hover:text-[#2D5864] hover:bg-[#FAF6EF]'
              } ${isSidebarCollapsed ? 'justify-center px-2' : ''}`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-105 ${
                  isActive ? 'text-white' : 'text-[#5F8E9C]'
                }`}
              />

              {!isSidebarCollapsed && (
                <span className="truncate flex-1 text-left">
                  {item.label}
                </span>
              )}

              {/* Status / Count indicator */}
              {!isSidebarCollapsed && item.badgeCount !== undefined && (
                <span
                  className={`px-1.5 py-0.5 text-[10px] font-mono rounded-md font-semibold ${
                    item.badgeAlert
                      ? 'bg-rose-100 text-rose-700'
                      : isActive
                      ? 'bg-white/20 text-white'
                      : 'bg-[#F2E8D8] text-[#2D5864]'
                  }`}
                >
                  {item.badgeCount}
                </span>
              )}

              {/* Collapsed dot badge */}
              {isSidebarCollapsed && item.badgeCount !== undefined && (
                <span
                  className={`absolute top-1.5 right-1.5 w-2 h-2 rounded-full ${
                    item.badgeAlert ? 'bg-rose-500' : 'bg-[#5F8E9C]'
                  }`}
                />
              )}
            </button>
          );
        })}
      </nav>

      {/* Quick Status in Footer */}
      {!isSidebarCollapsed ? (
        <div className="p-3 m-2.5 rounded-xl bg-[#FAF8F5] border border-[#F2E8D8] text-[11px] text-[#8C8C91]">
          <div className="flex items-center justify-between text-[#2D5864] font-medium">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Cadena de Custodia
            </span>
            <span className="font-mono text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
              Activa
            </span>
          </div>
        </div>
      ) : (
        <div className="p-2 border-t border-[#F2E8D8] flex justify-center text-[#8C8C91]">
          <span className="w-2 h-2 rounded-full bg-emerald-500" title="Cadena de Custodia: Activa"></span>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside
        className={`hidden md:block shrink-0 transition-all duration-200 z-30 h-screen sticky top-0 ${
          isSidebarCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Slide-Over Drawer */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-[#2D5864]/50 backdrop-blur-xs transition-opacity"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer Box */}
          <div className="relative w-72 max-w-[85vw] h-full shadow-2xl z-10 animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
