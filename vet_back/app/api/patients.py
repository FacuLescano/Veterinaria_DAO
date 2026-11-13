from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import obtener_sesion_bd
from app.schemas.patient import (
    ActualizacionEstadoTurno, ActualizarMascota, ActualizarResponsable,
    ActualizarTurno, ActualizarVeterinario, CrearConsulta, CrearMascota,
    CrearResponsable, CrearTurno, CrearVeterinario, LecturaConsulta,
    LecturaHistorialResponsablesMascota, LecturaHistorialTurno, LecturaMascota,
    LecturaResponsable, LecturaTurno, LecturaVeterinario,
    LecturaNotificacionVeterinario,
)
from app.models.notificacion import NotificacionVeterinario
from app.models.paciente import Veterinario
from app.services.patient_service import PatientService

router = APIRouter(prefix="/api/v1", tags=["Pacientes y atención"])


def get_service(db: Session = Depends(obtener_sesion_bd)) -> PatientService:
    return PatientService(db)


@router.get("/notificaciones", response_model=list[LecturaNotificacionVeterinario])
def listar_notificaciones(solo_no_leidas: bool = False, db: Session = Depends(obtener_sesion_bd)):
    # La bandeja general solo contiene los avisos del evento de verificación del precinto.
    consulta = select(NotificacionVeterinario).where(
        NotificacionVeterinario.estado_nuevo.in_(["aceptada", "rechazada"])
    )
    if solo_no_leidas:
        consulta = consulta.where(NotificacionVeterinario.leida_en.is_(None))
    return db.scalars(consulta.order_by(NotificacionVeterinario.creada_en.desc())).all()


@router.patch("/notificaciones/{notificacion_id}/leida", response_model=LecturaNotificacionVeterinario)
def marcar_notificacion_leida(notificacion_id: int, db: Session = Depends(obtener_sesion_bd)):
    notificacion = db.get(NotificacionVeterinario, notificacion_id)
    if notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if notificacion.leida_en is None:
        notificacion.leida_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notificacion)
    return notificacion


@router.post("/responsables", response_model=LecturaResponsable, status_code=status.HTTP_201_CREATED)
def crear_responsable(payload: CrearResponsable, service: PatientService = Depends(get_service)):
    return service.crear_responsable(payload)

@router.get("/responsables", response_model=list[LecturaResponsable])
def listar_responsables(search: str | None = None, service: PatientService = Depends(get_service)):
    return service.listar_responsables(search)

@router.get("/responsables/{responsible_id}", response_model=LecturaResponsable)
def obtener_responsable(responsible_id: int, service: PatientService = Depends(get_service)):
    return service.obtener_responsable(responsible_id)

@router.patch("/responsables/{responsible_id}", response_model=LecturaResponsable)
def actualizar_responsable(responsible_id: int, payload: ActualizarResponsable, service: PatientService = Depends(get_service)):
    return service.actualizar_responsable(responsible_id, payload)

@router.post("/veterinarios", response_model=LecturaVeterinario, status_code=status.HTTP_201_CREATED)
def crear_veterinario(payload: CrearVeterinario, service: PatientService = Depends(get_service)):
    return service.crear_veterinario(payload)

@router.get("/veterinarios", response_model=list[LecturaVeterinario])
def listar_veterinarios(service: PatientService = Depends(get_service)):
    return service.listar_veterinarios()

@router.patch("/veterinarios/{veterinarian_id}", response_model=LecturaVeterinario)
def actualizar_veterinario(veterinarian_id: int, payload: ActualizarVeterinario, service: PatientService = Depends(get_service)):
    return service.actualizar_veterinario(veterinarian_id, payload)

@router.get(
    "/veterinarios/{veterinarian_id}/notificaciones",
    response_model=list[LecturaNotificacionVeterinario],
)
def listar_notificaciones_veterinario(
    veterinarian_id: int,
    solo_no_leidas: bool = False,
    db: Session = Depends(obtener_sesion_bd),
):
    if db.get(Veterinario, veterinarian_id) is None:
        raise HTTPException(status_code=404, detail="Veterinario no encontrado")
    consulta = select(NotificacionVeterinario).where(
        NotificacionVeterinario.veterinario_id == veterinarian_id
    )
    if solo_no_leidas:
        consulta = consulta.where(NotificacionVeterinario.leida_en.is_(None))
    return db.scalars(consulta.order_by(NotificacionVeterinario.creada_en.desc())).all()

@router.patch(
    "/veterinarios/{veterinarian_id}/notificaciones/{notificacion_id}/leida",
    response_model=LecturaNotificacionVeterinario,
)
def marcar_notificacion_leida(
    veterinarian_id: int,
    notificacion_id: int,
    db: Session = Depends(obtener_sesion_bd),
):
    notificacion = db.get(NotificacionVeterinario, notificacion_id)
    if notificacion is None or notificacion.veterinario_id != veterinarian_id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if notificacion.leida_en is None:
        notificacion.leida_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notificacion)
    return notificacion

@router.post("/mascotas", response_model=LecturaMascota, status_code=status.HTTP_201_CREATED)
def crear_mascota(payload: CrearMascota, service: PatientService = Depends(get_service)):
    return service.crear_mascota(payload)

@router.get("/mascotas", response_model=list[LecturaMascota])
def listar_mascotas(responsible_id: int | None = None, search: str | None = None, service: PatientService = Depends(get_service)):
    return service.listar_mascotas(responsible_id, search)

@router.get("/mascotas/{pet_id}", response_model=LecturaMascota)
def obtener_mascota(pet_id: int, service: PatientService = Depends(get_service)):
    return service.obtener_mascota(pet_id)

@router.patch("/mascotas/{pet_id}", response_model=LecturaMascota)
def actualizar_mascota(pet_id: int, payload: ActualizarMascota, service: PatientService = Depends(get_service)):
    return service.actualizar_mascota(pet_id, payload)

@router.get("/mascotas/{pet_id}/responsables-historicos", response_model=list[LecturaHistorialResponsablesMascota])
def historial_responsables_mascota(pet_id: int, service: PatientService = Depends(get_service)):
    return service.historial_responsables_mascota(pet_id)

@router.post("/turnos", response_model=LecturaTurno, status_code=status.HTTP_201_CREATED)
def crear_turno(payload: CrearTurno, service: PatientService = Depends(get_service)):
    return service.crear_turno(payload)

@router.get("/turnos", response_model=list[LecturaTurno])
def listar_turnos(veterinarian_id: int | None = None, pet_id: int | None = None, from_date: datetime | None = Query(default=None), to_date: datetime | None = Query(default=None), service: PatientService = Depends(get_service)):
    return service.listar_turnos(veterinarian_id, pet_id, from_date, to_date)

@router.patch("/turnos/{appointment_id}", response_model=LecturaTurno)
def actualizar_turno(appointment_id: int, payload: ActualizarTurno, service: PatientService = Depends(get_service)):
    return service.actualizar_turno(appointment_id, payload)

@router.patch("/turnos/{appointment_id}/estado", response_model=LecturaTurno)
def actualizar_estado_turno(appointment_id: int, payload: ActualizacionEstadoTurno, service: PatientService = Depends(get_service)):
    return service.actualizar_estado_turno(appointment_id, payload)

@router.get("/turnos/{appointment_id}/historial", response_model=list[LecturaHistorialTurno])
def historial_turno(appointment_id: int, service: PatientService = Depends(get_service)):
    return service.historial_turno(appointment_id)

@router.post("/consultas", response_model=LecturaConsulta, status_code=status.HTTP_201_CREATED)
def crear_consulta(payload: CrearConsulta, service: PatientService = Depends(get_service)):
    return service.crear_consulta(payload)

@router.get("/consultas", response_model=list[LecturaConsulta])
def listar_consultas(pet_id: int | None = None, service: PatientService = Depends(get_service)):
    return service.listar_consultas(pet_id)

@router.get("/mascotas/{pet_id}/historia-clinica", response_model=list[LecturaConsulta])
def historia_clinica_mascota(pet_id: int, service: PatientService = Depends(get_service)):
    return service.historia_clinica_mascota(pet_id)
