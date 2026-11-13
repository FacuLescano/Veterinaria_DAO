import React, { useState, useEffect } from 'react';
import { VeterinariaProvider, useVeterinaria } from './context/VeterinariaContext';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Toast } from './components/common/Toast';
import { Modulo1Pacientes } from './components/modules/Modulo1Pacientes';
import { Modulo2OrdenesMuestras } from './components/modules/Modulo2OrdenesMuestras';
import { Modulo3PreparacionDespacho } from './components/modules/Modulo3PreparacionDespacho';
import { Modulo4RecepcionResultados } from './components/modules/Modulo4RecepcionResultados';
import { ModuloPythonExport } from './components/modules/ModuloPythonExport';
import { BandejaNotificaciones } from './components/modules/BandejaNotificaciones';
import { ArrowLeft, BookOpen } from 'lucide-react';

const AppContent: React.FC = () => {
  const { activeModule } = useVeterinaria();
  const [currentPath, setCurrentPath] = useState(() => window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const isDocsView = currentPath === '/docs' || currentPath === '/docs/' || window.location.hash.includes('docs');

  if (isDocsView) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] text-neutral-900 flex flex-col antialiased">
        {/* Docs Navigation Header */}
        <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-xs border-b border-[#E7E2DA] px-4 md:px-8 py-3.5 flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                window.history.pushState({}, '', '/');
                setCurrentPath('/');
              }}
              className="px-3 py-1.5 bg-[#FAF6EF] hover:bg-[#F2E8D8] text-[#2D5864] text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 border border-[#E7E2DA]"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Volver al Sistema de Gestión</span>
            </button>
            <div className="h-4 w-px bg-neutral-300"></div>
            <div className="flex items-center gap-2 text-xs">
              <span className="font-bold text-[#2D5864]">Patitas & Co.</span>
              <span className="text-neutral-400">/</span>
              <span className="text-neutral-600 font-medium flex items-center gap-1">
                <BookOpen className="w-3.5 h-3.5 text-[#5F8E9C]" />
                Documentación de Cátedra (/docs)
              </span>
            </div>
          </div>
          <span className="text-[11px] font-mono text-neutral-500 bg-neutral-100 px-2 py-0.5 rounded border border-neutral-200">
            POO · Patrones State & Observer
          </span>
        </header>

        {/* Docs Main Content */}
        <main className="flex-1 p-4 md:p-8 max-w-6xl w-full mx-auto">
          <ModuloPythonExport />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-neutral-900 flex flex-col md:flex-row antialiased">
      {/* Responsive Collapsible Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        <Header />

        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
          {activeModule === 'pacientes' && <Modulo1Pacientes />}
          {activeModule === 'ordenes' && <Modulo2OrdenesMuestras />}
          {activeModule === 'despacho' && <Modulo3PreparacionDespacho />}
          {activeModule === 'recepcion' && <Modulo4RecepcionResultados />}
          {activeModule === 'notificaciones' && <BandejaNotificaciones />}
        </main>

        {/* Minimal Footer */}
        <footer className="border-t border-[#E7E2DA] px-4 md:px-8 py-4 bg-white/70 text-xs text-neutral-500 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-[#2D5864]">Patitas & Co.</span>
            <span>· Red de Clínicas Veterinarias & Laboratorio Central</span>
          </div>
          <div className="text-[11px] text-neutral-400">
            Cadena de custodia biológica · Córdoba, Argentina
          </div>
        </footer>
      </div>

      {/* Toast Alert Feedback */}
      <Toast />
    </div>
  );
};

export default function App() {
  return (
    <VeterinariaProvider>
      <AppContent />
    </VeterinariaProvider>
  );
}
