from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dao.muestra_dao import MuestraDAO, TipoMuestraDAO
from app.dao.orden_analisis_dao import OrdenAnalisisDAO
from app.dao.tipo_analisis_dao import TipoAnalisisDAO
from app.models.orden_analisis import (
    DetalleOrdenAnalisis,
    HistorialMuestra,
    HistorialOrdenAnalisis,
    Muestra,
    OrdenAnalisis,
    TipoAnalisis,
    TipoMuestra,
)
from app.models.patient import Consultation, Veterinarian
from app.schemas.orden_analisis import (
    MuestraCreate,
    OrdenEstadoUpdate,
    SolicitudAnalisisCreate,
    TipoAnalisisCreate,
    TipoMuestraCreate,
)

ESTADOS_VALIDOS_ORDEN = {
    "solicitada",
    "en_preparacion",
    "enviada",
    "con_resultados",
    "cancelada",
}

TRANSICIONES_VALIDAS: dict[str, set[str]] = {
    "solicitada": {"en_preparacion", "cancelada"},
    "en_preparacion": {"enviada", "cancelada"},
    "enviada": {"con_resultados", "cancelada"},
    "con_resultados": set(),
    "cancelada": set(),
}


class OrdenAnalisisService:

    def __init__(self, db: Session):
        self.db = db
        self.orden_dao = OrdenAnalisisDAO(db)
        self.tipo_analisis_dao = TipoAnalisisDAO(db)
        self.muestra_dao = MuestraDAO(db)
        self.tipo_muestra_dao = TipoMuestraDAO(db)

    # --- Gestión de Tipos de Análisis (Catálogo) ---

    def crear_tipo_analisis(self, payload: TipoAnalisisCreate) -> TipoAnalisis:
        existente = self.tipo_analisis_dao.get_by_nombre(payload.nombre)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un tipo de análisis con el nombre '{payload.nombre}'",
            )
        tipo = TipoAnalisis(
            nombre=payload.nombre.strip(),
            descripcion=payload.descripcion.strip() if payload.descripcion else None,
            activo=True,
        )
        self.tipo_analisis_dao.create(tipo)
        self.db.commit()
        self.db.refresh(tipo)
        return tipo

    def listar_tipos_analisis(self, only_active: bool = True) -> list[TipoAnalisis]:
        return self.tipo_analisis_dao.list_all(only_active=only_active)

    # --- Crear y Solicitar Orden de Análisis ---

    def solicitar_analisis(self, payload: SolicitudAnalisisCreate) -> OrdenAnalisis:
        """
        Crea una orden de análisis formal vinculada a la consulta médica.
        Registra la orden con sus detalles y genera el primer evento en el historial.
        """
        # 1. Validar que la consulta médica exista
        consulta = self.db.get(Consultation, payload.consulta_id)
        if not consulta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consulta médica con ID {payload.consulta_id} no encontrada",
            )

        # 2. Identificar y validar al veterinario solicitante
        veterinario_id = payload.veterinario_id or consulta.veterinarian_id
        veterinario = self.db.get(Veterinarian, veterinario_id)
        if not veterinario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Veterinario con ID {veterinario_id} no encontrado",
            )
        if not veterinario.active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El veterinario solicitante no está activo",
            )

        # 3. Validar lista de análisis requeridos
        if not payload.detalles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Debe solicitar al menos un tipo de análisis",
            )

        # 4. Validar existencia y disponibilidad de cada TipoAnalisis solicitado
        detalles_entidad = []
        for det_payload in payload.detalles:
            tipo = self.tipo_analisis_dao.get_by_id(det_payload.tipo_analisis_id)
            if not tipo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El tipo de análisis con ID {det_payload.tipo_analisis_id} no existe",
                )
            if not tipo.activo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El tipo de análisis '{tipo.nombre}' no se encuentra disponible",
                )

            detalles_entidad.append(
                DetalleOrdenAnalisis(
                    tipo_analisis_id=det_payload.tipo_analisis_id,
                    indicaciones=det_payload.indicaciones,
                    estado="solicitado",
                )
            )

        # 5. Crear la orden de análisis en estado inicial 'solicitada'
        orden = OrdenAnalisis(
            consulta_id=consulta.id,
            veterinario_id=veterinario.id,
            estado="solicitada",
            observaciones=payload.observaciones,
            detalles=detalles_entidad,
        )
        self.orden_dao.create(orden)

        # 6. Registrar evento inicial en el historial
        historial_inicial = HistorialOrdenAnalisis(
            orden_id=orden.id,
            estado_anterior=None,
            estado_nuevo="solicitada",
            motivo="Orden creada y solicitada",
        )
        self.orden_dao.add_historial(historial_inicial)

        # 7. Persistir transacción
        self.db.commit()
        self.db.refresh(orden)

        return self.obtener_orden_por_id(orden.id)

    # --- Formalización y Gestión de Estados e Historial ---

    def actualizar_estado_orden(
        self, orden_id: int, payload: OrdenEstadoUpdate
    ) -> OrdenAnalisis:
        """
        Actualiza o formaliza el estado de la orden.
        Valida que la transición de estado sea permitida y registra el cambio en el historial.
        """
        orden = self.obtener_orden_por_id(orden_id)
        nuevo_estado = payload.nuevo_estado.lower().strip()

        if nuevo_estado not in ESTADOS_VALIDOS_ORDEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado '{nuevo_estado}' no válido. Estados permitidos: {', '.join(sorted(ESTADOS_VALIDOS_ORDEN))}",
            )

        if nuevo_estado == orden.estado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La orden ya se encuentra en estado '{orden.estado}'",
            )

        transiciones_permitidas = TRANSICIONES_VALIDAS.get(orden.estado, set())
        if nuevo_estado not in transiciones_permitidas:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Transición no permitida: no se puede cambiar de '{orden.estado}' a '{nuevo_estado}'. "
                    f"Transiciones válidas: {', '.join(sorted(transiciones_permitidas)) or 'Ninguna (estado final)'}"
                ),
            )

        estado_anterior = orden.estado
        orden.estado = nuevo_estado

        # Registrar en el historial de trazabilidad
        evento_historial = HistorialOrdenAnalisis(
            orden_id=orden.id,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            motivo=payload.motivo or f"Cambio de estado a {nuevo_estado}",
        )
        self.orden_dao.add_historial(evento_historial)

        self.db.commit()
        self.db.refresh(orden)
        return self.obtener_orden_por_id(orden.id)

    def obtener_historial_orden(self, orden_id: int) -> list[HistorialOrdenAnalisis]:
        """Consulta el historial de estados de una orden específica."""
        self.obtener_orden_por_id(orden_id)
        return self.orden_dao.get_historial(orden_id)

    # --- Consultas ---

    def obtener_orden_por_id(self, orden_id: int) -> OrdenAnalisis:
        orden = self.orden_dao.get_by_id(orden_id)
        if not orden:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Orden de análisis con ID {orden_id} no encontrada",
            )
        return orden

    def listar_ordenes(self, consulta_id: int | None = None) -> list[OrdenAnalisis]:
        if consulta_id is not None:
            return self.orden_dao.list_by_consulta_id(consulta_id)
        return self.orden_dao.list_all()

    # --- Gestión de Tipos de Muestra ---

    def crear_tipo_muestra(self, payload: TipoMuestraCreate) -> TipoMuestra:
        existente = self.tipo_muestra_dao.get_by_nombre(payload.nombre)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un tipo de muestra con el nombre '{payload.nombre}'",
            )
        tipo = TipoMuestra(
            nombre=payload.nombre.strip(),
            descripcion=payload.descripcion.strip() if payload.descripcion else None,
            condiciones_conservacion_default=(
                payload.condiciones_conservacion_default.strip()
                if payload.condiciones_conservacion_default
                else None
            ),
            activo=True,
        )
        self.tipo_muestra_dao.create(tipo)
        self.db.commit()
        self.db.refresh(tipo)
        return tipo

    def listar_tipos_muestra(self, only_active: bool = True) -> list[TipoMuestra]:
        return self.tipo_muestra_dao.list_all(only_active=only_active)

    # --- Extracción de Muestras Biológicas ---

    def registrar_extraccion_muestra(self, payload: MuestraCreate) -> Muestra:
        """
        Registra la obtención de una muestra biológica vinculada a una orden existente.
        Valida unicidad de código de etiqueta, existencia del tipo de muestra y genera
        el evento inicial de trazabilidad en el historial de la muestra.
        """
        # 1. Validar que la orden exista y no esté cancelada
        orden = self.obtener_orden_por_id(payload.orden_id)
        if orden.estado == "cancelada":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden registrar muestras para una orden cancelada",
            )

        # 2. Validar que el código de etiqueta no esté repetido
        codigo_limpio = payload.codigo_etiqueta.strip()
        muestra_existente = self.muestra_dao.get_by_codigo_etiqueta(codigo_limpio)
        if muestra_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una muestra registrada con el código de etiqueta '{codigo_limpio}'",
            )

        # 3. Validar tipo de muestra
        tipo_muestra = self.tipo_muestra_dao.get_by_id(payload.tipo_muestra_id)
        if not tipo_muestra:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El tipo de muestra con ID {payload.tipo_muestra_id} no existe",
            )
        if not tipo_muestra.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El tipo de muestra '{tipo_muestra.nombre}' no se encuentra disponible",
            )

        # 4. Determinar condiciones de conservación (específica o por defecto del tipo)
        condiciones = (
            payload.condiciones_conservacion.strip()
            if payload.condiciones_conservacion
            else (tipo_muestra.condiciones_conservacion_default or "Estándar a temperatura ambiente")
        )

        fecha_extraccion = payload.fecha_extraccion or datetime.now(timezone.utc)

        # 5. Instanciar y persistir la muestra en estado 'extraida'
        muestra = Muestra(
            codigo_etiqueta=codigo_limpio,
            orden_id=orden.id,
            tipo_muestra_id=tipo_muestra.id,
            responsable_extraccion=payload.responsable_extraccion.strip(),
            condiciones_conservacion=condiciones,
            observaciones_calidad=payload.observaciones_calidad.strip() if payload.observaciones_calidad else None,
            fecha_extraccion=fecha_extraccion,
            estado="extraida",
        )
        self.muestra_dao.create(muestra)

        # 6. Registrar evento inicial en el historial de la muestra
        evento_historial = HistorialMuestra(
            muestra_id=muestra.id,
            estado_anterior=None,
            estado_nuevo="extraida",
            motivo="Extracción de muestra registrada",
            responsable=payload.responsable_extraccion.strip(),
        )
        self.muestra_dao.add_historial(evento_historial)

        self.db.commit()
        return self.obtener_muestra_por_id(muestra.id)

    def obtener_muestra_por_id(self, muestra_id: int) -> Muestra:
        muestra = self.muestra_dao.get_by_id(muestra_id)
        if not muestra:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Muestra biológica con ID {muestra_id} no encontrada",
            )
        return muestra

    def listar_muestras_por_orden(self, orden_id: int) -> list[Muestra]:
        # Validar existencia de orden
        self.obtener_orden_por_id(orden_id)
        return self.muestra_dao.list_by_orden_id(orden_id)

