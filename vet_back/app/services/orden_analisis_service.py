from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dao.orden_analisis_dao import OrdenAnalisisDAO
from app.dao.tipo_analisis_dao import TipoAnalisisDAO
from app.models.orden_analisis import (
    DetalleOrdenAnalisis,
    OrdenAnalisis,
    TipoAnalisis,
)
from app.models.patient import Consultation, Veterinarian
from app.schemas.orden_analisis import (
    SolicitudAnalisisCreate,
    TipoAnalisisCreate,
)


class OrdenAnalisisService:

    def __init__(self, db: Session):
        self.db = db
        self.orden_dao = OrdenAnalisisDAO(db)
        self.tipo_analisis_dao = TipoAnalisisDAO(db)

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

    # --- US-06: Solicitar Análisis ---

    def solicitar_analisis(self, payload: SolicitudAnalisisCreate) -> OrdenAnalisis:
        """
        US-06: Solicitar uno o varios análisis vinculados a una consulta.
        Aplica las reglas de negocio y delega la persistencia al DAO.
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

        # 6. Persistir mediante el DAO
        self.orden_dao.create(orden)
        self.db.commit()
        self.db.refresh(orden)

        return self.obtener_orden_por_id(orden.id)

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
