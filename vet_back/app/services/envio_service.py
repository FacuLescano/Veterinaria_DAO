import json
from datetime import datetime, timezone
from html import escape
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dao.envio_dao import ConservadoraDAO, EnvioDAO
from app.dao.muestra_dao import MuestraDAO
from app.models.envio import (
    Conservadora,
    Envio,
    HistorialEnvio,
    IncidenciaTransporte,
    PrecintoSanitario,
    RegistroTemperatura,
    Remito,
    VerificacionPrecinto,
    envio_muestras,
)
from app.models.orden_analisis import HistorialMuestra, Muestra
from app.schemas.envio import (
    ConservadoraCreate,
    DespachoCreate,
    EnvioCreate,
    IncidenciaTransporteCreate,
    PrecintoCreate,
    RegistroTemperaturaCreate,
    VerificacionPrecintoCreate,
)


class EnvioService:
    def __init__(self, db: Session):
        self.db = db
        self.envio_dao = EnvioDAO(db)
        self.conservadora_dao = ConservadoraDAO(db)
        self.muestra_dao = MuestraDAO(db)

    def registrar_conservadora(self, payload: ConservadoraCreate) -> Conservadora:
        codigo = payload.codigo.strip()
        if self.conservadora_dao.get_by_codigo(codigo):
            raise HTTPException(status_code=409, detail="Ya existe una conservadora con ese código")
        conservadora = Conservadora(
            codigo=codigo,
            descripcion=payload.descripcion.strip() if payload.descripcion else None,
            disponible=True,
        )
        self.conservadora_dao.create(conservadora)
        self.db.commit()
        self.db.refresh(conservadora)
        return conservadora

    def listar_conservadoras(self) -> list[Conservadora]:
        return self.conservadora_dao.list_all()

    def crear_envio(self, payload: EnvioCreate) -> dict:
        if len({item.conservadora_id for item in payload.conservadoras}) != len(payload.conservadoras):
            raise HTTPException(status_code=400, detail="La solicitud repite una conservadora")

        asignaciones: dict[int, int] = {}
        conservadoras = []
        for contenido in payload.conservadoras:
            conservadora = self.conservadora_dao.get_by_id(contenido.conservadora_id)
            if not conservadora:
                raise HTTPException(
                    status_code=404,
                    detail=f"Conservadora con ID {contenido.conservadora_id} no encontrada",
                )
            if not conservadora.disponible:
                raise HTTPException(
                    status_code=409,
                    detail=f"La conservadora '{conservadora.codigo}' no está disponible",
                )
            conservadoras.append(conservadora)
            for muestra_id in contenido.muestra_ids:
                if muestra_id in asignaciones:
                    raise HTTPException(
                        status_code=400,
                        detail=f"La muestra {muestra_id} aparece más de una vez en el envío",
                    )
                asignaciones[muestra_id] = conservadora.id

        muestras = []
        for muestra_id in asignaciones:
            muestra = self.muestra_dao.get_by_id(muestra_id)
            if not muestra:
                raise HTTPException(status_code=404, detail=f"Muestra con ID {muestra_id} no encontrada")
            if muestra.estado != "lista_para_envio":
                raise HTTPException(
                    status_code=409,
                    detail=f"La muestra '{muestra.codigo_etiqueta}' debe estar lista_para_envio",
                )
            if not muestra.asociaciones_detalles:
                raise HTTPException(
                    status_code=400,
                    detail=f"La muestra '{muestra.codigo_etiqueta}' no está asociada a ningún análisis",
                )
            if not muestra.codigo_etiqueta.strip() or not muestra.condiciones_conservacion.strip():
                raise HTTPException(
                    status_code=400,
                    detail=f"La muestra '{muestra.codigo_etiqueta}' no tiene identificación o conservación registradas",
                )
            if muestra.envio:
                raise HTTPException(
                    status_code=409,
                    detail=f"La muestra '{muestra.codigo_etiqueta}' ya pertenece a un envío",
                )
            muestras.append(muestra)

        if not muestras:
            raise HTTPException(status_code=400, detail="El envío debe incluir al menos una muestra")

        envio = Envio(
            origen=payload.origen.strip(),
            destino=payload.destino.strip(),
            condiciones_empaquetado=payload.condiciones_empaquetado.strip(),
            estado="en_preparacion",
            observaciones=payload.observaciones.strip() if payload.observaciones else None,
            conservadoras=conservadoras,
        )
        self.envio_dao.create(envio)
        for conservadora in conservadoras:
            conservadora.disponible = False
        for muestra in muestras:
            self.db.execute(
                envio_muestras.insert().values(
                    envio_id=envio.id,
                    muestra_id=muestra.id,
                    conservadora_id=asignaciones[muestra.id],
                )
            )
            muestra.empaquetar(
                responsable=payload.responsable_preparacion,
                motivo=f"Empaquetada en el envío #{envio.id}",
            )
        self.db.add(
            HistorialEnvio(
                envio_id=envio.id,
                estado_anterior=None,
                estado_nuevo="en_preparacion",
                responsable="Sistema",
                observaciones="Envío creado para preparación",
            )
        )
        self.db.expire(envio, ["muestras"])
        self.db.commit()
        return self._serializar_envio(envio.id)

    def registrar_precinto(self, envio_id: int, payload: PrecintoCreate) -> dict:
        envio = self._get_envio_model(envio_id)
        self._validar_en_preparacion(envio)
        conservadora = self.conservadora_dao.get_by_id(payload.conservadora_id)
        if not conservadora or conservadora not in envio.conservadoras:
            raise HTTPException(
                status_code=404,
                detail="La conservadora no pertenece a este envío",
            )
        codigo = payload.codigo.strip()
        if self.envio_dao.get_precinto_by_code(codigo):
            raise HTTPException(status_code=409, detail="Ya existe un precinto con ese código")
        if self.envio_dao.get_precinto(envio_id, conservadora.id):
            raise HTTPException(
                status_code=409,
                detail="La conservadora ya tiene un precinto registrado para este envío",
            )
        envio.precintos.append(
            PrecintoSanitario(
                codigo=codigo,
                conservadora_id=conservadora.id,
                colocado_por=payload.colocado_por.strip(),
                fecha_colocacion=payload.fecha_colocacion or datetime.now(timezone.utc),
                estado="colocado",
            )
        )
        self.db.commit()
        return self._serializar_envio(envio_id)

    def verificar_precinto(
        self, envio_id: int, payload: VerificacionPrecintoCreate
    ) -> dict:
        envio = self._get_envio_model(envio_id)
        conservadora = self.conservadora_dao.get_by_id(payload.conservadora_id)
        if not conservadora or conservadora not in envio.conservadoras:
            raise HTTPException(status_code=404, detail="La conservadora no pertenece a este envío")

        precinto = self.envio_dao.get_precinto(envio_id, conservadora.id)
        if payload.resultado in {"integro", "roto", "codigo_no_coincide"} and not precinto:
            raise HTTPException(
                status_code=409,
                detail="No hay un precinto registrado para verificar en esta conservadora",
            )
        if payload.resultado == "integro":
            if not payload.codigo_observado:
                raise HTTPException(status_code=422, detail="Debe informar el código observado")
            if payload.codigo_observado != precinto.codigo:
                raise HTTPException(
                    status_code=409,
                    detail="El código observado no coincide; registre el resultado codigo_no_coincide",
                )
        if payload.resultado == "codigo_no_coincide":
            if not payload.codigo_observado:
                raise HTTPException(status_code=422, detail="Debe informar el código observado")
            if payload.codigo_observado == precinto.codigo:
                raise HTTPException(
                    status_code=422,
                    detail="El código observado coincide; use el resultado integro si el precinto está intacto",
                )

        verificacion = VerificacionPrecinto(
            envio_id=envio.id,
            conservadora_id=conservadora.id,
            precinto_id=precinto.id if precinto else None,
            codigo_observado=payload.codigo_observado,
            resultado=payload.resultado,
            fecha_verificacion=payload.fecha_verificacion or datetime.now(timezone.utc),
            responsable=payload.responsable.strip(),
            observaciones=payload.observaciones.strip() if payload.observaciones else None,
        )
        envio.verificaciones_precinto.append(verificacion)

        if payload.resultado != "integro":
            self.db.add(
                IncidenciaTransporte(
                    envio_id=envio.id,
                    conservadora_id=conservadora.id,
                    tipo=f"precinto_{payload.resultado}",
                    descripcion=(
                        payload.observaciones.strip()
                        if payload.observaciones
                        else f"Verificación del precinto: {payload.resultado}"
                    ),
                    fecha_evento=verificacion.fecha_verificacion,
                    responsable=payload.responsable.strip(),
                )
            )
        self.db.commit()
        return self._serializar_envio(envio_id)

    def despachar_envio(self, envio_id: int, payload: DespachoCreate) -> dict:
        envio = self._get_envio_model(envio_id)
        self._validar_en_preparacion(envio)
        if not envio.muestras:
            raise HTTPException(status_code=409, detail="No se puede despachar un envío sin muestras")
        if not envio.conservadoras:
            raise HTTPException(status_code=409, detail="El envío debe tener al menos una conservadora")

        precintos_por_conservadora = {p.conservadora_id for p in envio.precintos}
        conservadoras_sin_precinto = [
            c.codigo for c in envio.conservadoras if c.id not in precintos_por_conservadora
        ]
        if conservadoras_sin_precinto:
            raise HTTPException(
                status_code=409,
                detail="Falta registrar el precinto de estas conservadoras: " + ", ".join(conservadoras_sin_precinto),
            )

        verificaciones_por_conservadora = {}
        for verificacion in envio.verificaciones_precinto:
            actual = verificaciones_por_conservadora.get(verificacion.conservadora_id)
            if actual is None or verificacion.fecha_verificacion > actual.fecha_verificacion:
                verificaciones_por_conservadora[verificacion.conservadora_id] = verificacion
        verificaciones_con_problemas = [
            c.codigo
            for c in envio.conservadoras
            if c.id in verificaciones_por_conservadora
            and verificaciones_por_conservadora[c.id].resultado != "integro"
        ]
        if verificaciones_con_problemas:
            raise HTTPException(
                status_code=409,
                detail="Resuelva las verificaciones de precinto antes de despachar: "
                + ", ".join(verificaciones_con_problemas),
            )

        for muestra in envio.muestras:
            if muestra.estado == "lista_para_envio":
                # Compatibilidad con envíos en preparación creados antes de
                # incorporar el estado explícito Empaquetada.
                muestra.empaquetar(
                    responsable=payload.responsable_despacho,
                    motivo=f"Empaquetada en el envío #{envio.id}",
                )
            if muestra.estado != "empaquetada" or not muestra.asociaciones_detalles:
                raise HTTPException(
                    status_code=409,
                    detail=f"La muestra '{muestra.codigo_etiqueta}' ya no cumple los requisitos de despacho",
                )

        fecha_despacho = payload.fecha_despacho or datetime.now(timezone.utc)
        estado_anterior = envio.estado
        envio.estado = "despachado"
        envio.fecha_despacho = fecha_despacho
        envio.responsable_despacho = payload.responsable_despacho.strip()
        envio.transportista = payload.transportista.strip()
        if payload.observaciones:
            observacion = payload.observaciones.strip()
            envio.observaciones = "\n".join(filter(None, [envio.observaciones, observacion]))

        contenido = {
            "envio_id": envio.id,
            "origen": envio.origen,
            "destino": envio.destino,
            "condiciones_empaquetado": envio.condiciones_empaquetado,
            "fecha_despacho": fecha_despacho.isoformat(),
            "responsable_despacho": envio.responsable_despacho,
            "transportista": envio.transportista,
            "muestras": [
                {
                    "id": muestra.id,
                    "codigo_etiqueta": muestra.codigo_etiqueta,
                    "orden_id": muestra.orden_id,
                    "tipo_muestra": muestra.tipo_muestra.nombre,
                    "condiciones_conservacion": muestra.condiciones_conservacion,
                }
                for muestra in envio.muestras
            ],
            "conservadoras": [
                {
                    "id": conservadora.id,
                    "codigo": conservadora.codigo,
                    "muestra_ids": self._muestras_de_conservadora(envio.id, conservadora.id),
                    "precinto": next(
                        p.codigo for p in envio.precintos if p.conservadora_id == conservadora.id
                    ),
                }
                for conservadora in envio.conservadoras
            ],
        }
        numero_remito = f"REM-{fecha_despacho:%Y%m%d}-{uuid4().hex[:8].upper()}"
        envio.remito = Remito(
            numero=numero_remito,
            fecha_emision=datetime.now(timezone.utc),
            contenido_json=json.dumps(contenido, ensure_ascii=False),
        )

        for muestra in envio.muestras:
            muestra.despachar(
                responsable=payload.responsable_despacho,
                motivo=f"Despachada en remito {numero_remito}",
                fecha_evento=fecha_despacho,
            )

        self.db.add(
            HistorialEnvio(
                envio_id=envio.id,
                estado_anterior=estado_anterior,
                estado_nuevo="despachado",
                fecha_evento=fecha_despacho,
                responsable=payload.responsable_despacho.strip(),
                observaciones=payload.observaciones,
            )
        )
        self.db.commit()
        return self._serializar_envio(envio_id)

    def registrar_temperatura(self, envio_id: int, payload: RegistroTemperaturaCreate) -> dict:
        envio = self._get_envio_model(envio_id)
        if envio.estado != "despachado":
            raise HTTPException(status_code=409, detail="Las mediciones se registran durante el traslado")
        self._validar_referencias_transporte(envio, payload.conservadora_id, payload.muestra_id)
        envio.registros_temperatura.append(
            RegistroTemperatura(
                conservadora_id=payload.conservadora_id,
                muestra_id=payload.muestra_id,
                temperatura_requerida_c=payload.temperatura_requerida_c,
                temperatura_medida_c=payload.temperatura_medida_c,
                unidad=payload.unidad.strip(),
                fecha_medicion=payload.fecha_medicion,
                responsable=payload.responsable.strip(),
                dispositivo=payload.dispositivo.strip() if payload.dispositivo else None,
                observaciones=payload.observaciones.strip() if payload.observaciones else None,
            )
        )
        self.db.commit()
        return self._serializar_envio(envio_id)

    def registrar_incidencia(self, envio_id: int, payload: IncidenciaTransporteCreate) -> dict:
        envio = self._get_envio_model(envio_id)
        self._validar_referencias_transporte(envio, payload.conservadora_id, payload.muestra_id)
        envio.incidencias.append(
            IncidenciaTransporte(
                conservadora_id=payload.conservadora_id,
                muestra_id=payload.muestra_id,
                tipo=payload.tipo.strip(),
                descripcion=payload.descripcion.strip(),
                fecha_evento=payload.fecha_evento,
                responsable=payload.responsable.strip(),
            )
        )
        self.db.commit()
        return self._serializar_envio(envio_id)

    def listar_envios(self) -> list[dict]:
        return [self._serializar_envio(envio.id) for envio in self.envio_dao.list_all()]

    def obtener_envio(self, envio_id: int) -> dict:
        return self._serializar_envio(envio_id)

    def obtener_remito(self, envio_id: int) -> dict:
        envio = self._get_envio_model(envio_id)
        if not envio.remito:
            raise HTTPException(status_code=404, detail="El envío todavía no tiene remito de despacho")
        return {
            "id": envio.remito.id,
            "numero": envio.remito.numero,
            "envio_id": envio.remito.envio_id,
            "fecha_emision": envio.remito.fecha_emision,
            "contenido": json.loads(envio.remito.contenido_json),
        }

    def obtener_remito_html(self, envio_id: int) -> str:
        remito = self.obtener_remito(envio_id)
        contenido = remito["contenido"]
        muestras = {m["id"]: m for m in contenido["muestras"]}
        filas = []
        for conservadora in contenido["conservadoras"]:
            muestra_ids = conservadora["muestra_ids"]
            codigo_precinto = escape(conservadora["precinto"])
            for muestra_id in muestra_ids:
                muestra = muestras[muestra_id]
                filas.append(
                    "<tr>"
                    f"<td>{escape(conservadora['codigo'])}</td>"
                    f"<td>{codigo_precinto}</td>"
                    f"<td>{escape(muestra['codigo_etiqueta'])}</td>"
                    f"<td>{escape(muestra['tipo_muestra'])}</td>"
                    f"<td>{escape(muestra['condiciones_conservacion'])}</td>"
                    "</tr>"
                )
        return """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Remito {numero}</title>
<style>body{{font:14px Arial,sans-serif;margin:32px;color:#222}}h1{{margin-bottom:4px}}table{{border-collapse:collapse;width:100%;margin-top:20px}}th,td{{border:1px solid #999;padding:8px;text-align:left}}th{{background:#eee}}.meta{{line-height:1.7}}button{{padding:8px 14px;margin-bottom:20px}}@media print{{button{{display:none}}body{{margin:12mm}}}}</style>
</head><body><button onclick="window.print()">Imprimir remito</button>
<h1>Remito de envío</h1><p>Número: <strong>{numero}</strong></p>
<div class="meta"><div>Origen: {origen}</div><div>Destino: {destino}</div>
<div>Fecha de despacho: {fecha}</div><div>Responsable: {responsable}</div>
<div>Transportista: {transportista}</div><div>Condiciones de empaquetado: {condiciones}</div></div>
<table><thead><tr><th>Conservadora</th><th>Precinto</th><th>Muestra</th><th>Tipo</th><th>Conservación requerida</th></tr></thead>
<tbody>{filas}</tbody></table></body></html>""".format(
            numero=escape(remito["numero"]),
            origen=escape(contenido["origen"]),
            destino=escape(contenido["destino"]),
            fecha=escape(contenido["fecha_despacho"]),
            responsable=escape(contenido["responsable_despacho"]),
            transportista=escape(contenido["transportista"]),
            condiciones=escape(contenido["condiciones_empaquetado"]),
            filas="".join(filas),
        )

    def _get_envio_model(self, envio_id: int) -> Envio:
        envio = self.envio_dao.get_by_id(envio_id)
        if not envio:
            raise HTTPException(status_code=404, detail=f"Envío con ID {envio_id} no encontrado")
        return envio

    def _validar_en_preparacion(self, envio: Envio) -> None:
        if envio.estado != "en_preparacion":
            raise HTTPException(status_code=409, detail="El envío ya no está en preparación")

    def _validar_referencias_transporte(
        self, envio: Envio, conservadora_id: int | None, muestra_id: int | None
    ) -> None:
        if conservadora_id is not None and all(c.id != conservadora_id for c in envio.conservadoras):
            raise HTTPException(status_code=404, detail="La conservadora no pertenece a este envío")
        if muestra_id is not None and all(m.id != muestra_id for m in envio.muestras):
            raise HTTPException(status_code=404, detail="La muestra no pertenece a este envío")
        if conservadora_id is not None and muestra_id is not None:
            asignacion = self.db.execute(
                select(envio_muestras.c.muestra_id).where(
                    envio_muestras.c.envio_id == envio.id,
                    envio_muestras.c.conservadora_id == conservadora_id,
                    envio_muestras.c.muestra_id == muestra_id,
                )
            ).first()
            if not asignacion:
                raise HTTPException(
                    status_code=400,
                    detail="La muestra no está asignada a esa conservadora en este envío",
                )

    def _muestras_de_conservadora(self, envio_id: int, conservadora_id: int) -> list[int]:
        query = select(envio_muestras.c.muestra_id).where(
            envio_muestras.c.envio_id == envio_id,
            envio_muestras.c.conservadora_id == conservadora_id,
        )
        return list(self.db.scalars(query).all())

    def _serializar_envio(self, envio_id: int) -> dict:
        envio = self._get_envio_model(envio_id)
        conservadoras = []
        for conservadora in envio.conservadoras:
            conservadoras.append(
                {
                    "conservadora": conservadora,
                    "muestra_ids": self._muestras_de_conservadora(envio.id, conservadora.id),
                    "precintos": [
                        precinto for precinto in envio.precintos
                        if precinto.conservadora_id == conservadora.id
                    ],
                }
            )
        remito = None
        if envio.remito:
            remito = {
                "id": envio.remito.id,
                "numero": envio.remito.numero,
                "envio_id": envio.remito.envio_id,
                "fecha_emision": envio.remito.fecha_emision,
                "contenido": json.loads(envio.remito.contenido_json),
            }
        return {
            "id": envio.id,
            "origen": envio.origen,
            "destino": envio.destino,
            "transportista": envio.transportista,
            "responsable_despacho": envio.responsable_despacho,
            "estado": envio.estado,
            "fecha_creacion": envio.fecha_creacion,
            "fecha_despacho": envio.fecha_despacho,
            "condiciones_empaquetado": envio.condiciones_empaquetado,
            "observaciones": envio.observaciones,
            "muestras": envio.muestras,
            "conservadoras": conservadoras,
            "precintos": envio.precintos,
            "remito": remito,
            "historial": envio.historial,
            "registros_temperatura": envio.registros_temperatura,
            "incidencias": envio.incidencias,
        }
