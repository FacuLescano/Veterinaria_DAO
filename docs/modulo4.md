# Módulo 4: recepción, incidencias y resultados

El paquete funciona de forma independiente y se monta desde `app.main` bajo `/api/v1`. Mantiene tablas propias (`m4_*`) y referencias externas por identificador; no declara ni modifica envíos, muestras, órdenes, detalles de orden o pacientes que pertenecen a otros módulos.

## Contrato con el módulo 3

`integracion.py` define `EnvioDespachado`, la proyección mínima que el módulo 3 debe entregar: identificador, fecha de despacho, remito, identificadores de muestras y conservadoras, y precintos. Al integrar esa rama, se reemplaza `listar_envios_despachados()` por el adaptador a su DAO/API. El contrato es deliberadamente de lectura.

## Contrato con el módulo 2

Las recepciones comparan el contenido efectivo con la lista despachada del remito. Los resultados guardan `orden_id`, `detalle_orden_id`, `muestra_id` y `paciente_id` como referencias del módulo 2/1. La capa de integración debe comprobar esos identificadores contra los módulos propietarios antes de habilitar la carga en producción; este módulo no crea entidades sustitutas ni relaciones con tablas ajenas.

## Endpoints

- `GET /api/v1/envios-pendientes`
- `POST /api/v1/recepciones`, `GET /api/v1/recepciones/{id}`
- `POST /api/v1/verificaciones-precinto`, `GET /api/v1/verificaciones-precinto?envio_id=...`
- `POST /api/v1/incidencias`, `GET /api/v1/incidencias`, `POST /api/v1/incidencias/{id}/resolver`
- `POST /api/v1/resultados`, `GET /api/v1/resultados`, `PATCH /api/v1/resultados/{id}/estado`, `PATCH /api/v1/resultados/{id}/interpretacion`

Las anomalías de contenido y precinto crean incidencias con trazabilidad. La carga de informes recibe `informe_uri` y nombre como metadatos; el almacenamiento binario y la autorización del archivo corresponden a la infraestructura común del proyecto.

La base se configura con `MODULO4_DATABASE_URL` o `MODULO4_DATABASE_PATH`; por defecto usa `vet_back/data/modulo4.db`. `MODULO4_DATABASE_URL` permite compartir el motor de la aplicación manteniendo tablas con prefijo propio.
