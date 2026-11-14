import { ActiveModule } from '../context/VeterinariaContext';

export type ReporteTabId = 'reporte1' | 'reporte2' | 'reporte3' | 'reporte4';

export interface RouteInfo {
  module: ActiveModule;
  reporteTab?: ReporteTabId;
  isDocs: boolean;
}

export const MODULE_ROUTES: Record<ActiveModule, string> = {
  pacientes: '/pacientes',
  ordenes: '/ordenes',
  despacho: '/despacho',
  recepcion: '/recepcion',
  notificaciones: '/notificaciones',
  reportes: '/reportes/1',
  python: '/docs',
};

export const REPORTE_ROUTES: Record<ReporteTabId, string> = {
  reporte1: '/reportes/1',
  reporte2: '/reportes/2',
  reporte3: '/reportes/3',
  reporte4: '/reportes/4',
};

export function parseCurrentRoute(): RouteInfo {
  if (typeof window === 'undefined') {
    return { module: 'pacientes', isDocs: false };
  }

  const path = window.location.pathname.toLowerCase().replace(/\/+$/, '') || '/';
  const hash = window.location.hash.toLowerCase();

  if (path === '/docs' || path.startsWith('/docs/') || hash.includes('docs')) {
    return { module: 'python', isDocs: true };
  }

  if (path.startsWith('/reportes') || hash.includes('reportes')) {
    let tab: ReporteTabId = 'reporte1';

    if (
      path.includes('/reportes/2') ||
      path.includes('rechazadas') ||
      path.includes('bioseguridad') ||
      hash.includes('reporte2') ||
      hash.includes('/2')
    ) {
      tab = 'reporte2';
    } else if (
      path.includes('/reportes/3') ||
      path.includes('rendimiento') ||
      path.includes('clinico') ||
      hash.includes('reporte3') ||
      hash.includes('/3')
    ) {
      tab = 'reporte3';
    } else if (
      path.includes('/reportes/4') ||
      path.includes('eficacia') ||
      path.includes('diagnostica') ||
      hash.includes('reporte4') ||
      hash.includes('/4')
    ) {
      tab = 'reporte4';
    } else if (
      path.includes('/reportes/1') ||
      path.includes('sla') ||
      path.includes('transito') ||
      hash.includes('reporte1') ||
      hash.includes('/1')
    ) {
      tab = 'reporte1';
    }

    return { module: 'reportes', reporteTab: tab, isDocs: false };
  }

  if (path.startsWith('/ordenes') || hash.includes('ordenes')) {
    return { module: 'ordenes', isDocs: false };
  }
  if (path.startsWith('/despacho') || hash.includes('despacho')) {
    return { module: 'despacho', isDocs: false };
  }
  if (path.startsWith('/recepcion') || hash.includes('recepcion')) {
    return { module: 'recepcion', isDocs: false };
  }
  if (path.startsWith('/notificaciones') || hash.includes('notificaciones')) {
    return { module: 'notificaciones', isDocs: false };
  }

  return { module: 'pacientes', isDocs: false };
}

export function navigateToRoute(targetPath: string, replace = false): void {
  if (typeof window === 'undefined') return;

  const currentPath = window.location.pathname;
  if (currentPath !== targetPath) {
    if (replace) {
      window.history.replaceState({}, '', targetPath);
    } else {
      window.history.pushState({}, '', targetPath);
    }
    window.dispatchEvent(new Event('popstate'));
  }
}

