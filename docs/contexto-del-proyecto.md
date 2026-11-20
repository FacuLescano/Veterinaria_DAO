# Contexto del proyecto · Patitas & Co.

Esta guía describe el código de la rama `integracion-frontend` en la revisión `9707719`. Las rutas registradas, los esquemas y los servicios son la referencia para interpretar el comportamiento actual.

## Qué resuelve el sistema

Patitas & Co. es una aplicación web de gestión veterinaria. La operación comienza con un responsable, su mascota y una consulta. Si el veterinario pide estudios, la orden vincula la atención clínica con el rotulado de las muestras, su despacho documentado y la recepción informada por el laboratorio. Los resultados vuelven a la orden y alimentan los avisos y reportes. El laboratorio se integra desde el sistema veterinario mediante carga manual o un adaptador simulado de consulta de resultados.

```text
Responsable → Mascota → Consulta (turno opcional)
                            ↓
                     Orden de análisis → Detalles de estudios
                            ↓                   ↕ asociación
                          Muestras ─────────────┘
                            ↓
               Envío → Conservadoras y precintos → Remito
                            ↓
               Verificación de llegada y recepción
                            ↓
                 Resultados → Avisos y reportes
```

## Arquitectura y puntos de entrada

| Capa | Archivos y responsabilidad |
| --- | --- |
| Aplicación web | [main.tsx](../vet_front/src/main.tsx) monta React. [App.tsx](../vet_front/src/App.tsx) monta el proveedor y selecciona el módulo. Vite empaqueta el frontend TypeScript con Tailwind CSS y Lucide React. |
| Estado y contrato del frontend | [VeterinariaContext.tsx](../vet_front/src/context/VeterinariaContext.tsx) concentra la carga, las mutaciones y la conversión de las respuestas de la API a [tipos de pantalla](../vet_front/src/types/veterinaria.ts). Los reportes y la bandeja también hacen sus propias consultas HTTP. |
| API | [app/main.py](../vet_back/app/main.py) monta FastAPI y los routers de `app/api/`. Los esquemas Pydantic están en `app/schemas/`. Swagger se genera a partir de las rutas registradas. |
| Reglas y persistencia | `app/services/` coordina validaciones y escrituras. `app/dao/` contiene `OrdenAnalisisDAO`, `TipoAnalisisDAO`, `TipoMuestraDAO`, `MuestraDAO`, `AsociacionMuestraDAO`, `EnvioDAO` y `ConservadoraDAO`. Pacientes, recepción y reportes consultan SQLAlchemy directamente desde sus servicios o rutas. |
| Dominio e integraciones | `app/models/` define el ORM. [estados_muestra.py](../vet_back/app/state/estados_muestra.py) contiene el patrón State. `app/observers/` publica los eventos de muestra y resultados. `app/core/` carga la configuración y contiene los adaptadores de despacho y laboratorio. |

[db/session.py](../vet_back/app/db/session.py) define `Base`, `engine` y `SessionLocal`. [db/recepcion.py](../vet_back/app/db/recepcion.py) define `BaseModulo4` y una fábrica de sesiones propia sobre el mismo motor. En SQLite local, todas las tablas operativas comparten `vet_back/data/veterinaria.db` cuando se inicia desde `vet_back/`. En los módulos 1–3 predominan los IDs enteros. Las tablas `m4_*` generan UUID de texto para sus propios registros y guardan referencias a IDs operativos como cadenas.

Al arrancar, `lifespan` crea las tablas de ambos metadatos y adapta esquemas anteriores. Agrega `condiciones_empaquetado` a `envios` y `weight_kg` y `photo_url` a `mascotas` cuando faltan. En SQLite también reemplaza la restricción histórica de horario de turnos. Estas migraciones están en [main.py](../vet_back/app/main.py).

## Flujo y clases principales

### 1. Pacientes y atención clínica

[Modelos de pacientes](../vet_back/app/models/paciente.py) · [PatientService](../vet_back/app/services/patient_service.py) · [Router](../vet_back/app/api/patients.py) · [Pantalla](../vet_front/src/components/modules/Modulo1Pacientes.tsx)

- `Responsable` es el contacto actual de una o más `Mascota`. Su documento es único. `HistorialResponsableMascota` conserva los períodos de titularidad cuando se cambia el responsable.
- `Veterinario` tiene matrícula y estado activo. `Turno` vincula mascota, profesional, fecha y duración. `HistorialTurno` registra altas, reprogramaciones y cambios de estado. Al crear un turno o cambiar su horario se valida que sea futuro y que el profesional esté activo y disponible. La comprobación de solapamiento considera los turnos `pendiente` y `confirmado`. Los estados `atendido`, `cancelado` y `ausente` cierran el turno para cambios manuales posteriores.
- `Consulta` pertenece a una mascota y un veterinario. Puede registrarse espontáneamente o referenciar un turno. Si lleva turno, el servicio exige que corresponda a la misma mascota y al mismo profesional, rechaza los turnos cancelados y marca como `atendido` el turno asociado al guardar. La relación permite una consulta por turno. La historia clínica se obtiene consultando las consultas de la mascota.

### 2. Órdenes y muestras

[Modelos de órdenes y muestras](../vet_back/app/models/orden_analisis.py) · [OrdenAnalisisService](../vet_back/app/services/orden_analisis_service.py) · [Router](../vet_back/app/api/ordenes_analisis.py) · [Pantalla](../vet_front/src/components/modules/Modulo2OrdenesMuestras.tsx)

- `OrdenAnalisis` nace de una `Consulta` y contiene uno o más `DetalleOrdenAnalisis`. Cada detalle representa un estudio de catálogo (`TipoAnalisis`). El veterinario de la orden se toma de la consulta por defecto y debe estar activo. El paciente se obtiene a través de la consulta. El frontend puede crear una consulta con el motivo «Solicitud de análisis clínicos» si al pedir los estudios no encuentra una adecuada.
- `Muestra` representa el material rotulado de una orden. Tiene código de etiqueta único, tipo de material (`TipoMuestra`), responsable de extracción y condiciones de conservación. Al registrar la primera extracción, una orden `solicitada` pasa a `en_preparacion`.
- `AsociacionDetalleMuestra` vincula cada muestra con uno o más detalles de la misma orden. Se admite más de una muestra por detalle. El servicio comprueba el catálogo de tipos compatibles si el análisis tiene compatibilidades configuradas. La vinculación se hace antes del empaquetado. En la UI, al vincular una muestra extraída se solicita también el cambio a `lista_para_envio`.
- La orden y sus detalles tienen estados propios. El flujo habitual de la orden es `solicitada` → `en_preparacion` → `enviada` → `con_resultados`, con cancelación disponible desde los tres primeros estados. Los detalles recorren `solicitado` → `con_muestra` → `resultado_listo`. `HistorialOrdenAnalisis` y `HistorialMuestra` almacenan los eventos registrados para cada entidad.

#### State de la muestra

`Muestra` reconstruye su objeto `EstadoMuestra` desde el código guardado y le delega cada transición. Al aceptar una transición actualiza el código y añade una entrada a `HistorialMuestra` con fecha, responsable y motivo. Los estados concretos se pueden leer en [estados_muestra.py](../vet_back/app/domain/estados_muestra.py).

| Código persistido | Transiciones relevantes |
| --- | --- |
| `extraida` | Admite iniciar preparación o pasar directamente a `lista_para_envio`. |
| `pendiente_preparacion` | Admite pasar a `lista_para_envio`. |
| `lista_para_envio` | Pasa a `empaquetada` al crear un envío válido. |
| `empaquetada` | Pasa a `enviada` al despachar. |
| `enviada` | Representa `EstadoEnTransito`, que también reconoce `en_transito` al reconstruirse. Pasa a `recibida` al registrar la llegada. |
| `recibida` | Puede pasar a `analizada` con referencia al resultado o a `rechazada` con motivo. |
| `con_inconveniente` | Puede alcanzarse desde los estados anteriores a `analizada` y `rechazada`. Volver a `lista_para_envio` requiere un motivo, y la pertenencia previa a un envío sigue afectando la elegibilidad de despacho. |
| `analizada`, `rechazada` | Estados terminales del patrón State. |

El `PATCH` público del módulo 2 sirve para preparación e inconvenientes. El empaquetado y el tránsito se gestionan con las operaciones de envío. La recepción y el análisis se actualizan desde el módulo 4.

### 3. Preparación, despacho y trazabilidad

[Modelos de envío](../vet_back/app/models/envio.py) · [EnvioService](../vet_back/app/services/envio_service.py) · [Router](../vet_back/app/api/envios.py) · [Pantalla](../vet_front/src/components/modules/Modulo3PreparacionDespacho.tsx)

- `Envio` agrupa muestras en una o más `Conservadora`. Cada muestra puede pertenecer a un solo envío y se asigna a una conservadora concreta. Para prepararlo, las conservadoras deben estar disponibles y las muestras listas, rotuladas, con conservación registrada y asociadas a algún estudio. El alta reserva las conservadoras y empaqueta las muestras.
- `PrecintoSanitario` tiene código único y se coloca uno por conservadora del envío. `VerificacionPrecinto` del módulo 3 documenta comprobaciones de despacho. Una anomalía crea una `IncidenciaTransporte`. El despacho exige que todas las conservadoras tengan precinto y bloquea aquellas cuya última verificación registrada indica una anomalía. Colocar el precinto basta si todavía no hay una verificación registrada.
- Al despachar, el envío pasa a `despachado`, las muestras a `enviada` y las órdenes correspondientes que estaban `en_preparacion` pasan a `enviada`. `Remito` guarda una copia histórica del contenido a esa fecha, con condiciones de empaquetado, conservadoras, precintos y datos de transporte. El servicio expone JSON y una versión HTML imprimible. `HistorialEnvio`, `RegistroTemperatura` e `IncidenciaTransporte` completan la trazabilidad.
- El botón de despacho del frontend valida la temperatura de salida, crea el envío, registra la medición, registra el precinto y despacha. La API admite la medición durante la preparación y antes de registrar el precinto de esa conservadora. Los intervalos de refrigeración y temperatura ambiente incluyen sus límites. Las muestras congeladas requieren −20 °C o menos.

### 4. Recepción y resultados

[Modelos de recepción](../vet_back/app/models/recepcion.py) · [Servicios](../vet_back/app/services/recepcion.py) · [Router](../vet_back/app/api/recepcion.py) · [Pantalla](../vet_front/src/components/modules/Modulo4RecepcionResultados.tsx)

- `EnvioDespachado`, en [recepcion_integracion.py](../vet_back/app/core/recepcion_integracion.py), proyecta los envíos despachados junto con remito, muestras, conservadoras y precintos. `RecepcionEnvio` admite una recepción por envío. Valida que la lista despachada coincida con el envío original y que las muestras recibidas pertenezcan a esa lista. Una recepción puede ser `completa` o `parcial`. Al registrarla, se liberan las conservadoras. Las muestras en tránsito que llegan pasan a `recibida` y las faltantes generan incidencias.
- La `VerificacionPrecinto` de este módulo registra la condición a la llegada. Un precinto roto, ausente u otra anomalía, incluida la diferencia entre código esperado y observado, genera una `Incidencia`. Las muestras que aún están `enviada` pasan a `con_inconveniente`. La bandeja registra la recepción como `aceptada` o `rechazada` según la verificación. La UI también muestra «Rechazada» de inmediato en el caso anómalo, mientras que el estado operativo persistido por esa verificación es `con_inconveniente`.
- La UI encadena verificación y recepción en dos llamadas y declara recibido el contenido completo del remito en la segunda. La API admite informar un subconjunto de muestras. Una recepción parcial puede seguir figurando en `/envios-pendientes`, aunque el servicio devuelve `409` si se intenta registrar una segunda recepción para ese envío. El estado del `Envio` de despacho permanece `despachado` y la situación de llegada se consulta en los registros del módulo 4.
- La carga manual de `ResultadoAnalisis` verifica la correspondencia entre orden, detalle y paciente, y comprueba duplicados según la identidad del informe. Puede registrar valores y conclusión en `datos`, nombre o URI del informe e interpretación clínica. El resultado nace `recibido` y admite `en_revision` y `validado`. Un detalle con resultado pasa a `resultado_listo` y la orden pasa a `con_resultados` cuando todos sus detalles están listos. Si se vincula una muestra en estado `recibida`, el registro también la pasa a `analizada`.
- [LaboratorioGateway](../vet_back/app/core/laboratorio_gateway.py) tipa la integración externa. El router usa `LaboratorioMock` con los escenarios `completo`, `multiples` (predeterminado), `pendientes`, `sin_resultados` e `invalido`. `GET` permite consultar una respuesta sin persistirla. `POST` exige una muestra `recibida`, valida que los detalles coincidan con sus asociaciones y registra el lote de resultados, los cambios de estado y la trazabilidad en una transacción. Una respuesta pendiente o sin datos deja intactos los registros. Los duplicados y las respuestas inconsistentes se rechazan.

### Avisos mediante Observer

| Evento | Efecto |
| --- | --- |
| `CambioEstadoMuestra` | `Muestra` publica la transición a `SujetoEstadoMuestra` cuando está asociada a una sesión. El sujeto general arranca sin observadores suscritos. `NotificarVeterinario` es una implementación disponible. |
| `RecepcionMuestra` | Después de guardar la verificación de precinto, `VeterinarioObserver` guarda una `NotificacionVeterinario` por muestra para el profesional de la orden. La bandeja general filtra a los avisos de verificación. |
| `ResultadosRegistrados` / `ResultadoAnalisisRegistrado` | Después de guardar el resultado manual o el lote, `ResponsableMascotaObserver` busca el correo del responsable y delega en `ServicioCorreo`. El aviso informa la disponibilidad de resultados. Un fallo al publicar el evento o al enviar el correo deja vigente el resultado guardado. |

Código de referencia en [observers/muestra.py](../vet_back/app/observers/muestra.py), [observers/resultados.py](../vet_back/app/observers/resultados.py) y [correo_service.py](../vet_back/app/services/correo_service.py).

### Reportes

[Router de reportes](../vet_back/app/api/reportes.py) · [ReportesService](../vet_back/app/services/reportes_service.py) · [Servicios de cálculo y exportación](../vet_back/app/services/reportes/) · [Pantallas](../vet_front/src/components/modules/reportes/)

`ReportesService` delega en cuatro servicios especializados. Los reportes se calculan con datos operativos al solicitarlos. Cada reporte expone JSON, Excel con `openpyxl`, PDF con ReportLab y envío por correo con adjuntos seleccionables. Las fechas de filtro usan `YYYY-MM-DD`.

| Ruta bajo `/api/v1/reportes` | Qué mide y cómo se filtra |
| --- | --- |
| `/tiempos-sla` | Tiempo de despacho a recepción, de recepción a resultado y total. El cumplimiento compara el tiempo total con una matriz de horas por tipo de análisis y prioridad. Hoy toma el primer estudio de la orden y deduce la urgencia de sus observaciones. Filtros por fecha de despacho, tipo de análisis, transportista y prioridad. |
| `/muestras-rechazadas` | Auditoría de aceptación y rechazo, causas de incidencias, precintos, cadena de frío y desempeño por transportista. Combina datos de despacho y recepción. Filtros por fecha, causa, transportista y estado auditado. |
| `/rendimiento-clinico` | Actividad de agenda y atención por veterinario, estados de turnos, derivaciones y estudios solicitados. Filtros por fecha, veterinario, especialidad, estado de turno y derivación. |
| `/eficacia-diagnostica` | Clasifica resultados según sus parámetros y alertas y agrupa hallazgos por especie y edad. Filtros por fecha, especie, grupo etario, clasificación y tipo de análisis. La confirmación del diagnóstico presuntivo aparece sin valor calculado porque falta una conclusión clínica posterior comparable. |

## Referencia de endpoints

Las rutas de la tabla llevan el prefijo `/api/v1`. `GET /`, `GET /health`, `/openapi.json`, `/docs` y `/redoc` se sirven desde la raíz del backend. Los contratos combinan nombres como `pet_id` y `veterinarian_id` en atención con `orden_id`, `muestra_id` y `envio_id` en laboratorio y transporte. Los nombres de cada payload se pueden consultar en Swagger o en `app/schemas/`.

| Área | Método y ruta | Uso |
| --- | --- | --- |
| Responsables | `GET`, `POST /responsables` · `GET`, `PATCH /responsables/{id}` | Alta, búsqueda (`search`), detalle y edición. |
| Veterinarios | `GET`, `POST /veterinarios` · `PATCH /veterinarios/{id}` | Alta, listado y actualización, incluida la activación. |
| Mascotas | `GET`, `POST /mascotas` · `GET`, `PATCH /mascotas/{id}` · `GET /mascotas/{id}/responsables-historicos` | Alta, búsqueda o filtro por responsable, edición e historial. |
| Agenda | `GET`, `POST /turnos` · `PATCH /turnos/{id}` · `PATCH /turnos/{id}/estado` · `GET /turnos/{id}/historial` | Agenda filtrable por profesional, mascota y fechas, reprogramación y estados. |
| Consultas | `GET`, `POST /consultas` · `GET /mascotas/{id}/historia-clinica` · `GET /consultas/{id}/analisis` | Atención clínica, historia del paciente y órdenes de una consulta. |
| Catálogos | `GET`, `POST /tipos-analisis` · `GET`, `POST /tipos-muestra` · `POST /tipos-analisis/{id}/compatibilidad` | Configuración de estudios, materiales y compatibilidad. |
| Órdenes | `GET`, `POST /ordenes-analisis` · `POST /ordenes-analisis/solicitar` · `GET /ordenes-analisis/{id}` · `PATCH /ordenes-analisis/{id}/estado` · `GET /ordenes-analisis/{id}/historial` | Creación, consulta, transición explícita e historial. Las dos rutas de alta delegan en el mismo servicio. |
| Muestras | `POST /muestras` · `GET /muestras/{id}` · `PATCH /muestras/{id}/estado` · `GET /muestras/{id}/historial` | Extracción, consulta y trazabilidad de una muestra. |
| Vínculo y seguimiento | `POST /ordenes-analisis/{id}/asociar-muestra` · `GET /ordenes-analisis/{id}/muestras` · `GET /ordenes-analisis/{id}/analisis-pendientes` · `GET /ordenes-analisis/{id}/seguimiento` | Vincular con `muestra_id` y `detalle_ids`, y consultar el avance de la orden. |
| Preparación | `GET`, `POST /conservadoras` · `GET`, `POST /envios` · `GET /envios/{id}` | Catálogo de conservadoras, armado de envíos y detalle de trazabilidad. |
| Despacho | `POST /envios/{id}/temperaturas` · `POST /envios/{id}/precintos` · `POST /envios/{id}/verificaciones-precinto` · `POST /envios/{id}/despachar` | Medición de salida antes del precinto, colocación, verificación y despacho. |
| Traslado y remito | `POST /envios/{id}/incidencias` · `GET /envios/{id}/remito` · `GET /envios/{id}/remito/impresion` | Registro de incidencias y consulta del remito en JSON o HTML. |
| Llegada | `GET /envios-pendientes` · `GET`, `POST /verificaciones-precinto` · `POST /recepciones` · `GET /recepciones/{id}` | Bandeja de envíos, verificación de llegada y constancia de recepción. El GET de verificaciones requiere `envio_id`. |
| Incidencias de llegada | `GET`, `POST /incidencias` · `POST /incidencias/{id}/resolver` | Registro y resolución. El listado admite `envio_id` y `abiertas`. |
| Resultados | `GET`, `POST /resultados` · `PATCH /resultados/{id}/estado` · `PATCH /resultados/{id}/interpretacion` | Consulta y carga manual, revisión e interpretación. El listado admite `orden_id`, `paciente_id` y `estado`. |
| Laboratorio simulado | `GET`, `POST /muestras/{id}/resultados-laboratorio` | Consultar o incorporar el lote de resultados con `?escenario=...`. |
| Bandeja general | `GET /notificaciones` · `PATCH /notificaciones/{notificacion_id}/leida` | Ver avisos de verificación y marcarlos como leídos. El GET admite `solo_no_leidas`. |
| Bandeja por profesional | `GET /veterinarios/{id}/notificaciones` · `PATCH /veterinarios/{id}/notificaciones/{notificacion_id}/leida` | Listar y marcar avisos de un veterinario concreto. |
| Reportes | `GET /reportes/{reporte}` · `GET /reportes/{reporte}/excel` · `GET /reportes/{reporte}/pdf` · `POST /reportes/{reporte}/enviar-email` | Consultar métricas, descargar archivos o enviarlos por SMTP. `{reporte}` es una de las cuatro rutas de la sección anterior. |

El backend usa habitualmente `404` para entidades inexistentes, `409` para conflictos de estado o duplicados y `422` para validaciones. Los routers operativos están expuestos sin dependencias de autenticación. Los nombres e IDs de responsables informados en las operaciones forman parte de los registros de trazabilidad.

## Frontend y comportamiento al recargar

- [navigation.ts](../vet_front/src/utils/navigation.ts) lee el path y el hash y actualiza la navegación con History API. Los accesos principales son `/pacientes`, `/ordenes`, `/despacho`, `/recepcion`, `/notificaciones` y `/reportes/1` a `/reportes/4`. `/docs` en el puerto del frontend muestra [material de cátedra y descarga de ejemplos Tkinter](../vet_front/src/components/modules/ModuloPythonExport.tsx). `/docs` en el puerto del backend es Swagger.
- `VeterinariaContext` hidrata las pantallas con llamadas paralelas a la API. Carga las muestras a partir de las órdenes, transforma los IDs a cadenas para la UI e inicializa por API los tipos de muestra, tipos de análisis y conservadoras de catálogo que falten. También busca o da de alta veterinarios al guardar ciertas operaciones. El estado operativo se recupera de SQLite vía API. [mockData.ts](../vet_front/src/data/mockData.ts) conserva datos de ejemplo sin participación en la hidratación actual.
- La UI actualiza algunas vistas localmente después de las escrituras. Para verificar qué sobrevivirá a una recarga, conviene revisar la respuesta del endpoint o repetir la consulta. Esto importa especialmente en las secuencias de despacho y recepción y en las etiquetas de estado mostradas por pantalla.

## Uso local y verificación

Backend, desde la raíz en PowerShell y con un entorno virtual propio del backend.

```powershell
cd vet_back
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, en una segunda terminal desde la raíz.

```powershell
cd vet_front
npm ci
npm run dev
```

El frontend se abre en `http://localhost:3000` y la API en `http://127.0.0.1:8000`. [vite.config.ts](../vet_front/vite.config.ts) reenvía `/api` y `/health` en desarrollo. Se puede cambiar el destino con `VITE_API_PROXY_TARGET` en `vet_front/.env.local`. Si se sirve el build estático, el servidor debe resolver esas rutas hacia la API y servir la SPA para la navegación directa a sus pantallas.

| Configuración | Comportamiento |
| --- | --- |
| `DATABASE_URL` | Conexión SQLAlchemy explícita, con prioridad sobre `DATABASE_PATH`. |
| `DATABASE_PATH` | Ruta SQLite. El valor inicial `./data/veterinaria.db` se resuelve desde el directorio de trabajo. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_SECURITY` | Configuración para avisos y reportes por correo. `SMTP_SECURITY` acepta `starttls`, `ssl` y `none`. La aplicación puede iniciar sin SMTP. |

[configuracion.py](../vet_back/app/core/configuracion.py) carga primero `vet_back/.env` y luego el `.env` de la raíz. Tienen prioridad las variables ya definidas en el entorno. Los nombres de las variables SMTP están en [.env.example](../vet_back/.env.example).

- **Backend**. Ejecutar `python -m pytest` con las dependencias instaladas desde `vet_back/`. [vet_back/test/](../vet_back/test/) cubre agenda y consultas, órdenes, State de muestras, preparación y despacho, escenarios del laboratorio, observers y los cuatro reportes. [conftest.py](../vet_back/test/conftest.py) prepara SQLite en memoria para las pruebas y sustituye la dependencia de sesión principal en su cliente HTTP.
- **Frontend**. Ejecutar `npm run build` desde `vet_front/` para verificar TypeScript y compilar el paquete estático con Vite.
