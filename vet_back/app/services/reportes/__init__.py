"""Módulo de servicios especializados para Reportes y Analítica de Gestión."""
from app.services.reportes.servicio_tiempos_sla import ServicioTiemposSla
from app.services.reportes.servicio_muestras_rechazadas import ServicioMuestrasRechazadas

__all__ = ["ServicioTiemposSla", "ServicioMuestrasRechazadas"]

