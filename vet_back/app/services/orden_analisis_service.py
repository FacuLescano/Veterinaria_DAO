from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dao.muestra_dao import AsociacionMuestraDAO, MuestraDAO, TipoMuestraDAO
from app.dao.orden_analisis_dao import OrdenAnalisisDAO
from app.dao.tipo_analisis_dao import TipoAnalisisDAO
from app.domain.estados_muestra import TransicionMuestraInvalida
from app.models.orden_analisis import (
    AsociacionDetalleMuestra,
    DetalleOrdenAnalisis,
    HistorialMuestra,
    HistorialOrdenAnalisis,
    Muestra,
    OrdenAnalisis,
    TipoAnalisis,
    TipoMuestra,
)
from app.models.patient import Consulta, Veterinario
from app.schemas.orden_analisis import (
    AsociarMuestraAnalisisCreate,
    ConfigurarCompatibilidadCreate,
    MuestraCreate,
    MuestraEstadoUpdate,
    OrdenEstadoUpdate,
    ResultadoAsociacionRead,
    ResumenEstadoMuestrasRead,
    SeguimientoOrdenMuestrasRead,
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

ESTADOS_VALIDOS_MUESTRA = {
    "extraida",
    "pendiente_preparacion",
    "lista_para_envio",
    "enviada",
    "con_inconveniente",
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
        self.asociacion_dao = AsociacionMuestraDAO(db)

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
        if payload.tipos_muestra_compatibles_ids:
            for tmid in payload.tipos_muestra_compatibles_ids:
                tm = self.tipo_muestra_dao.get_by_id(tmid)
                if tm:
                    tipo.tipos_muestra_compatibles.append(tm)

        self.tipo_analisis_dao.create(tipo)
        self.db.commit()
        self.db.refresh(tipo)
        return tipo

    def configurar_compatibilidad(
        self, tipo_analisis_id: int, payload: ConfigurarCompatibilidadCreate
    ) -> TipoAnalisis:
        """Configura los tipos de muestra biológica compatibles con un tipo de análisis."""
        tipo = self.tipo_analisis_dao.get_by_id(tipo_analisis_id)
        if not tipo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tipo de análisis con ID {tipo_analisis_id} no encontrado",
            )
        compatibles = []
        for tmid in payload.tipos_muestra_ids:
            tm = self.tipo_muestra_dao.get_by_id(tmid)
            if not tm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tipo de muestra con ID {tmid} no existe",
                )
            compatibles.append(tm)
        tipo.tipos_muestra_compatibles = compatibles
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
        consulta = self.db.get(Consulta, payload.consulta_id)
        if not consulta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consulta médica con ID {payload.consulta_id} no encontrada",
            )

        # 2. Identificar y validar al veterinario solicitante
        veterinario_id = payload.veterinario_id or consulta.veterinarian_id
        veterinario = self.db.get(Veterinario, veterinario_id)
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

    # --- Asociación Muestras con Análisis ---

    def asociar_muestra_con_analisis(
        self, orden_id: int, payload: AsociarMuestraAnalisisCreate
    ) -> ResultadoAsociacionRead:
        """
        Vincula una muestra biológica con los análisis (detalles) que puede satisfacer.
        - Valida que la muestra y los análisis pertenezcan a la misma orden.
        - Valida compatibilidad biológica entre el tipo de análisis y el tipo de muestra.
        - Permite que una misma muestra satisfaga múltiples análisis compatibles.
        """
        orden = self.obtener_orden_por_id(orden_id)
        if orden.estado == "cancelada":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden asociar muestras a una orden cancelada",
            )

        muestra = self.obtener_muestra_por_id(payload.muestra_id)
        if muestra.orden_id != orden.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La muestra con ID {muestra.id} no pertenece a la orden #{orden.id}",
            )

        detalles_dict = {d.id: d for d in orden.detalles}
        asociados = []

        for detalle_id in payload.detalle_ids:
            if detalle_id not in detalles_dict:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El análisis solicitado con ID {detalle_id} no pertenece a la orden #{orden.id}",
                )
            detalle = detalles_dict[detalle_id]

            # Validar compatibilidad si el tipo de análisis tiene restricciones configuradas
            if detalle.tipo_analisis.tipos_muestra_compatibles:
                compatibles_ids = {tm.id for tm in detalle.tipo_analisis.tipos_muestra_compatibles}
                if muestra.tipo_muestra_id not in compatibles_ids:
                    nombres_compatibles = ", ".join(
                        tm.nombre for tm in detalle.tipo_analisis.tipos_muestra_compatibles
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Incompatibilidad biológica: el análisis '{detalle.tipo_analisis.nombre}' "
                            f"requiere [{nombres_compatibles}], y no es compatible con el tipo de muestra '{muestra.tipo_muestra.nombre}'"
                        ),
                    )

            # Verificar si ya existe la asociación
            existente = self.asociacion_dao.get_by_detalle_and_muestra(detalle.id, muestra.id)
            if not existente:
                nueva_asociacion = AsociacionDetalleMuestra(
                    detalle_id=detalle.id,
                    muestra_id=muestra.id,
                    observaciones=payload.observaciones,
                )
                self.asociacion_dao.create(nueva_asociacion)
                detalle.estado = "con_muestra"

            asociados.append(detalle.id)

        self.db.commit()
        return ResultadoAsociacionRead(
            muestra_id=muestra.id,
            detalles_asociados=asociados,
            mensaje=f"Muestra '{muestra.codigo_etiqueta}' asociada correctamente a {len(asociados)} análisis",
        )

    def listar_analisis_pendientes_muestra(self, orden_id: int) -> list[DetalleOrdenAnalisis]:
        """
        US-09: Identifica análisis de una orden que todavía no cuentan con una muestra adecuada asignada.
        """
        orden = self.obtener_orden_por_id(orden_id)
        return [d for d in orden.detalles if not d.asociaciones_muestras]

    # --- Gestión y Consulta de Estado de Muestras y Orden ---

    def actualizar_estado_muestra(
        self, muestra_id: int, payload: MuestraEstadoUpdate
    ) -> Muestra:
        """
        US-10: Actualiza el estado de una muestra biológica y registra la trazabilidad en su historial.
        Criterio: No se permite enviar muestras sin identificación o sin la información obligatoria.
        """
        muestra = self.obtener_muestra_por_id(muestra_id)
        nuevo_estado = payload.nuevo_estado.lower().strip()

        if nuevo_estado not in ESTADOS_VALIDOS_MUESTRA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado '{nuevo_estado}' no válido para la muestra. Estados permitidos: {', '.join(sorted(ESTADOS_VALIDOS_MUESTRA))}",
            )

        if nuevo_estado == muestra.estado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La muestra ya se encuentra en estado '{muestra.estado}'",
            )

        # Regla de aceptación US-10: No se permite enviar muestras sin identificación o información obligatoria
        if nuevo_estado == "enviada":
            if not muestra.codigo_etiqueta or not muestra.codigo_etiqueta.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se permite enviar muestras sin identificación física (código de etiqueta)",
                )
            if not muestra.responsable_extraccion or not muestra.responsable_extraccion.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se permite enviar muestras sin responsable de extracción registrado",
                )
            if not muestra.condiciones_conservacion or not muestra.condiciones_conservacion.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se permite enviar muestras sin condiciones de conservación especificadas",
                )
            if not muestra.asociaciones_detalles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se permite enviar una muestra que no esté asociada a ningún análisis solicitado",
                )
            if not muestra.envio:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El despacho debe registrarse mediante la creación de un envío con remito y precinto",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El despacho debe registrarse desde la operación de despacho del envío",
            )

        try:
            muestra.transicionar_a_estado(
                nuevo_estado,
                payload.motivo,
                responsable=payload.responsable,
            )
        except TransicionMuestraInvalida as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        self.db.commit()
        self.db.refresh(muestra)
        return self.obtener_muestra_por_id(muestra.id)

    def obtener_historial_muestra(self, muestra_id: int) -> list[HistorialMuestra]:
        """US-10: Consulta el historial cronológico de cambios de estado de una muestra."""
        self.obtener_muestra_por_id(muestra_id)
        return self.muestra_dao.get_historial(muestra_id)

    def consultar_estado_orden_y_muestras(self, orden_id: int) -> SeguimientoOrdenMuestrasRead:
        """
        US-10: Consultar el estado de una orden y sus muestras para conocer cuáles están listas para enviar
        y cuáles tienen inconvenientes.
        """
        orden = self.obtener_orden_por_id(orden_id)

        # Categorizar muestras según su estado
        registradas = [m for m in orden.muestras if m.estado == "extraida"]
        pendientes_prep = [m for m in orden.muestras if m.estado == "pendiente_preparacion"]
        listas_para_envio = [m for m in orden.muestras if m.estado == "lista_para_envio"]
        empaquetadas = [m for m in orden.muestras if m.estado == "empaquetada"]
        enviadas = [m for m in orden.muestras if m.estado == "enviada"]
        con_inconvenientes = [m for m in orden.muestras if m.estado == "con_inconveniente"]

        # Análisis que no cuentan todavía con una muestra asociada
        analisis_sin_muestra = [d for d in orden.detalles if not d.asociaciones_muestras]

        # Resumen numérico
        resumen = ResumenEstadoMuestrasRead(
            total=len(orden.muestras),
            registradas=len(registradas),
            pendientes_preparacion=len(pendientes_prep),
            listas_para_envio=len(listas_para_envio),
            empaquetadas=len(empaquetadas),
            enviadas=len(enviadas),
            con_inconvenientes=len(con_inconvenientes),
        )

        # Determinar si la orden está en condiciones de ser despachada
        # Condiciones: hay muestras, todos los análisis tienen muestra, ninguna muestra tiene inconveniente
        # y todas las muestras están listas, empaquetadas o ya enviadas.
        lista_para_despacho = (
            len(orden.muestras) > 0
            and len(analisis_sin_muestra) == 0
            and len(con_inconvenientes) == 0
            and len(pendientes_prep) == 0
            and len(registradas) == 0
            and all(
                muestra.estado in {"lista_para_envio", "empaquetada", "enviada"}
                for muestra in orden.muestras
            )
        )

        return SeguimientoOrdenMuestrasRead(
            orden_id=orden.id,
            estado_orden=orden.estado,
            paciente_nombre=orden.paciente_nombre,
            resumen_muestras=resumen,
            muestras_listas_para_enviar=listas_para_envio,
            muestras_pendientes_preparacion=pendientes_prep,
            muestras_con_inconvenientes=con_inconvenientes,
            analisis_sin_muestra=analisis_sin_muestra,
            lista_para_despacho=lista_para_despacho,
        )



