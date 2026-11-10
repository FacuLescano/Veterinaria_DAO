[[Proyecto]]
# Tecnologias
[[Vet-Repo]]
# Análisis del dominio: Veterinaria — Red de clínicas y derivación de laboratorio

El dominio planteado en el PDF consiste en desarrollar un sistema para una red de clínicas veterinarias que permita gestionar la atención médica de las mascotas y la derivación de muestras biológicas a un laboratorio central, garantizando la trazabilidad de las muestras desde su extracción hasta la obtención del diagnóstico.

El núcleo del sistema no es solamente la atención veterinaria, sino también el transporte seguro de las muestras, el control de su cadena de custodia y el registro de los resultados. Para abarcar el dominio correctamente, es necesario modelar tanto la parte clínica como la logística, relacionando ambas mediante las órdenes de derivación y las muestras.

A continuación, separo lo que establece el PDF de las ampliaciones de modelado que convendría considerar para el trabajo práctico.

## 1. Flujo principal del dominio

1. Registrar al cliente y su mascota

Se identifica al responsable y se registra la mascota con su historia clínica.

2. Atender a la mascota

Un veterinario registra la consulta, el examen clínico y las indicaciones.

3. Extraer la muestra y emitir la derivación

Si se necesita un análisis complejo, se genera una orden de derivación asociada a la consulta y a la muestra.

4. Empaquetar y documentar

La muestra se coloca en una conservadora isotérmica y se generan el remito biológico y el precinto sanitario.

5. Transportar la muestra

Se registran los movimientos y los estados del envío para mantener la trazabilidad.

6. Recibir y validar en el laboratorio

Se verifica el estado del precinto. Si llega roto, la muestra se rechaza y no puede procesarse.

7. Analizar, registrar resultados y cerrar la atención

El laboratorio registra los resultados y el sistema permite emitir los comprobantes de atención.

Este flujo resume los siete procesos obligatorios de la consigna. El PDF también exige registrar la historia clínica, controlar las vacunas obligatorias, evitar superposiciones de turnos y mantener un historial inmutable de los estados de cada muestra.


Importante: el flujo puede interrumpirse si una muestra es rechazada. En ese caso, el sistema debe registrar el motivo y conservar la trazabilidad del incidente. No debería permitir que una muestra rechazada continúe al análisis como si hubiera sido recibida correctamente.

## 2. Entidades principales y su función

Una entidad representa un elemento del dominio sobre el cual el sistema necesita almacenar información, identificarlo y relacionarlo con otros elementos.

La siguiente propuesta combina los conceptos expresamente mencionados en el PDF con entidades que recomiendo incorporar para que el modelo pueda representar el flujo completo.

Las entidades marcadas como ampliación son propuestas de modelado; no aparecen necesariamente con ese nombre en la consigna.

### A. Gestión de clientes y atención clínica

1. Cliente / Responsable

Representa a la persona responsable de una o más mascotas. Permite identificar quién solicita la atención, recibir comunicaciones y asociar las mascotas con su propietario o responsable legal.

Atributos sugeridos: id, nombre, apellido, documento, teléfono, correo electrónico y domicilio.

2. Mascota

Representa al paciente veterinario. Debe tener obligatoriamente un responsable asociado. Es el elemento que vincula las consultas, la historia clínica, las vacunas, los tratamientos y las muestras tomadas.

Atributos sugeridos: id, nombre, especie, raza, sexo, fecha de nacimiento aproximada, peso e identificación por microchip si corresponde.

3. Historia Clínica

Contiene los antecedentes médicos de la mascota y permite consultar la evolución a lo largo del tiempo. Puede reunir consultas, diagnósticos, alergias, vacunas, tratamientos y resultados de laboratorio.

Relación: cada mascota tiene una historia clínica, que acumula información de múltiples atenciones.

4. Consulta Médica

Registra una atención concreta: fecha, motivo, evaluación clínica, diagnóstico presuntivo, indicaciones y profesional responsable. Es el punto de partida de una posible derivación al laboratorio.

Una consulta puede no requerir análisis; por eso, la derivación no debería ser obligatoria en todas las consultas.

5. Profesional Veterinario

Representa al profesional que realiza la atención, registra hallazgos, solicita estudios e interpreta resultados para tomar decisiones clínicas.

Ampliación de modelado: permite identificar quién realizó cada acción y en qué clínica trabaja.

### B. Gestión de la derivación y el transporte

Esta parte es especialmente importante porque la consigna indica que el ciclo de vida de la muestra y del remito biológico será evaluado críticamente.


6. Orden de Derivación

Formaliza la solicitud de análisis. Se origina en una consulta y especifica qué estudios se necesitan, para qué mascota y qué clínica solicita el servicio.

Atributos sugeridos: número de orden, fecha, estudios solicitados, prioridad, profesional solicitante y estado.

7. Muestra Biológica

Representa el material extraído de la mascota que debe analizarse. Es una entidad central del dominio, ya que su identificación, conservación, transporte y estados deben poder seguirse durante todo el proceso.

Atributos sugeridos: identificador único, tipo de muestra, fecha y hora de extracción, persona que la extrajo, condiciones de conservación y estado actual.

8. Conservadora Isotérmica / Contenedor

Representa el recipiente que protege las muestras durante el transporte y permite mantener las condiciones de conservación requeridas.

Atributos sugeridos: código identificador, tipo, capacidad, condiciones térmicas requeridas y estado de disponibilidad.

9. Remito Biológico

Documenta el envío de muestras desde una clínica hacia el laboratorio. Debe permitir identificar el contenido del envío, su origen, destino, fecha y recepción.

Atributos sugeridos: número único, fecha de emisión, clínica de origen, laboratorio de destino y estado del envío.

10. Precinto Sanitario

Identifica el cierre de seguridad del contenedor. Su integridad debe verificarse al recibir el envío, ya que un precinto roto impide procesar la muestra.

Atributos sugeridos: código único, fecha de colocación, responsable de colocación, estado de integridad y fecha de verificación.

11. Envío / Registro de Transporte

Representa el traslado de la muestra o del contenedor. Permite registrar los eventos logísticos que ocurren entre la salida de la clínica y la recepción en el laboratorio.

Ampliación de modelado: puede incluir transportista, fechas y horas de despacho y entrega, incidencias y condiciones de transporte.

### C. Procesamiento y resultado

12. Clínica Veterinaria

Representa cada establecimiento de la red. Permite determinar dónde se atendió a la mascota, dónde se tomó la muestra y qué clínica solicitó la derivación.

Atributos sugeridos: código, nombre, dirección, teléfono y datos de contacto.

13. Laboratorio Central

Es el establecimiento receptor de las muestras. Valida la recepción, verifica el precinto, acepta o rechaza las muestras y realiza los estudios autorizados.

Puede modelarse como entidad o como establecimiento especializado si se necesita representar varios laboratorios.

14. Análisis de Laboratorio

Representa un estudio solicitado, su ejecución y su estado de procesamiento. Es conveniente separarlo de la muestra, porque una muestra podría utilizarse para varios análisis compatibles.

Atributos sugeridos: tipo de análisis, fecha de inicio, fecha de finalización, profesional responsable y estado.

15. Resultado de Análisis

Almacena los valores obtenidos, las unidades, los rangos de referencia y las observaciones del laboratorio. Se vincula con el análisis que lo produjo y, de forma indirecta, con la muestra y la mascota.

Debe conservarse el vínculo con el estudio correspondiente para evitar atribuir un resultado a otra muestra o paciente.

16. Comprobante de Atención

Registra los conceptos facturados por la atención clínica y los servicios de laboratorio, según corresponda. Permite respaldar los importes cobrados y elaborar reportes económicos.

Ampliación de modelado: conviene contemplar conceptos, importes, fecha de emisión, pagos y estado de cancelación.

## 3. Relaciones principales entre las entidades

Las relaciones describen cómo se conectan los objetos del dominio y qué cardinalidad tienen. Las siguientes cardinalidades son una propuesta de diseño razonable, no restricciones explícitas en todos los casos del PDF.

|Relación|Cardinalidad sugerida|Función|
|---|---|---|
|Cliente — Mascota|1 a N|Un responsable puede tener varias mascotas; cada mascota debe tener al menos un responsable asociado.|
|Mascota — Historia Clínica|1 a 1|Cada mascota tiene su historia clínica.|
|Mascota — Consulta Médica|1 a N|Una mascota puede recibir muchas consultas a lo largo del tiempo.|
|Veterinario — Consulta|1 a N|Un profesional puede registrar numerosas consultas.|
|Clínica — Consulta|1 a N|Cada consulta se realiza en una clínica determinada.|
|Consulta — Orden de Derivación|1 a 0..N|Una consulta puede no derivar muestras o generar una o varias órdenes.|
|Orden de Derivación — Muestra|1 a 1..N|Una orden puede involucrar una o más muestras.|
|Remito Biológico — Muestra|1 a N|Un remito documenta el envío de una o varias muestras.|
|Remito — Contenedor|N a M, si se permite reutilización y agrupamiento|Un envío puede involucrar varios contenedores y un contenedor puede utilizarse en envíos distintos a lo largo del tiempo.|
|Contenedor — Precinto|1 a N histórico|Un contenedor puede tener distintos precintos a lo largo de su vida útil, pero debe identificarse el precinto colocado en cada envío.|
|Remito — Envío|1 a 1 o 1 a N|Depende de si el remito representa un único traslado o puede cubrir varios tramos de transporte.|
|Muestra — Análisis|1 a N|Una muestra puede someterse a varios estudios compatibles.|
|Análisis — Resultado|1 a 1 o 1 a N|Depende de si cada análisis genera un resultado único o múltiples determinaciones.|
|Consulta — Comprobante|1 a 0..N|Una atención puede generar uno o varios comprobantes, según la política de facturación.|

### Esquema conceptual resumido

![[DAO/Drawing 2026-10-09 13.21.43.excalidraw.md#^group=iwu3ktSPuzESMH_9Af1-v]]


Este esquema muestra la ruta principal, pero no pretende reemplazar un diagrama de clases UML. En el diseño definitivo deberán definirse las multiplicidades, los atributos, las operaciones y las restricciones de cada asociación.

## 4. Aspectos importantes que conviene agregar al dominio

El PDF es una descripción simplificada. Para construir un sistema consistente con Programación Orientada a Objetos, hay varias situaciones que deberían analizarse antes de implementar las clases.

### 4.1. Diferenciar los estados de la muestra, el envío y el análisis

Este es uno de los puntos más importantes del diseño.

La consigna define los estados de la muestra como:

- Extraída.
    
- Empaquetada.
    
- En tránsito.
    
- Recibida.
    
- Analizada.
    

Además, si el precinto está roto, debe cambiar al estado Muestra Rechazada.

Sin embargo, no conviene usar un único estado para representar todo el proceso. Una muestra puede estar correctamente recibida mientras el análisis está pendiente, y el envío puede estar entregado aunque algunas muestras hayan sido rechazadas.

Por eso, recomiendo separar:

|Objeto|Ejemplos de estados propuestos|
|---|---|
|Muestra biológica|Extraída, Empaquetada, En tránsito, Recibida, Analizada, Rechazada|
|Remito biológico|En preparación, Emitido, Despachado, Recibido, Cerrado, Con incidencias|
|Análisis|Pendiente, En proceso, Finalizado, Cancelado|
|Comprobante|Pendiente de pago, Pagado, Anulado|

Los estados adicionales son propuestas para el modelo, no una lista completa definida por el PDF.

Regla fundamental: los cambios de estado de la muestra deben registrarse de forma inmutable. Esto significa que no se debe sobrescribir el historial para que parezca que un estado anterior nunca existió. Si se comete un error, debe registrarse una corrección o un evento adicional que conserve la evidencia original.

### 4.2. Modelar el historial de estados como una entidad

En lugar de guardar únicamente el estado actual de una muestra, sería conveniente crear una entidad `HistorialEstadoMuestra` o `EventoTrazabilidad`.

Atributos posibles:

- Identificador.
    
- Muestra asociada.
    
- Estado anterior y estado nuevo.
    
- Fecha y hora del cambio.
    
- Usuario o responsable que realizó la operación.
    
- Ubicación donde ocurrió.
    
- Observación o motivo del cambio.
    

Esto permite reconstruir qué sucedió en cualquier momento y elaborar reportes de tiempos de tránsito, retrasos e incidentes.

También sería útil registrar eventos de transporte independientes de los estados: salida de la clínica, recepción por el transportista, llegada al laboratorio y entrega efectiva.

### 4.3. Controlar la viabilidad de las muestras 

No alcanza con verificar si una muestra existe y tiene un precinto intacto. Dependiendo del análisis solicitado, también puede ser necesario controlar:

- Tipo de muestra requerido.
    
- Cantidad o volumen mínimo.
    
- Fecha y hora de extracción.
    
- Tiempo máximo admisible hasta el procesamiento.
    
- Temperatura y condiciones de conservación.
    
- Identificación correcta del paciente.
    
- Envase, rotulado y condiciones sanitarias.
    

Estos controles dependen del tipo de muestra y del estudio solicitado. El sistema debería permitir configurar las reglas correspondientes, en lugar de asumir que todas las muestras requieren las mismas condiciones.

### 4.4. Resolver situaciones excepcionales

El flujo principal describe un caso exitoso, pero un sistema real necesita gestionar alternativas.

|Situación|Comportamiento recomendado|
|---|---|
|El precinto llega roto|Rechazar la muestra, registrar la evidencia y bloquear el procesamiento.|
|La muestra llega tarde|Evaluar si continúa siendo viable según las reglas del análisis.|
|La muestra no coincide con la orden|Bloquear su aceptación hasta resolver la discrepancia.|
|El envío contiene varias muestras y una está dañada|Registrar el resultado individual de cada muestra sin rechazar automáticamente las demás.|
|Se pierde una muestra durante el transporte|Registrar la incidencia y mantener el envío y la muestra identificables.|
|El laboratorio no puede realizar el estudio|Registrar el motivo y definir si corresponde una nueva derivación o extracción.|
|El resultado necesita corrección|Conservar el resultado original y registrar la rectificación con su responsable y fecha.|

Estos casos son ampliaciones propuestas y deben acordarse con las reglas de negocio que defina el equipo.

### 4.5. Diferenciar los tipos de profesionales y sus permisos

No todos los usuarios del sistema deberían poder realizar las mismas operaciones.

Se podrían definir roles como:

- Recepcionista: administra clientes, mascotas y turnos.
    
- Veterinario: registra consultas, diagnósticos y órdenes de derivación.
    
- Técnico de laboratorio: registra recepción, procesamiento y resultados.
    
- Responsable de logística: administra contenedores, remitos y transporte.
    
- Administrador: gestiona usuarios, parámetros y catálogos.
    
- Responsable de facturación: consulta servicios y registra comprobantes y pagos.
    

Esto introduce control de acceso y permite identificar quién realizó cada operación.

### 4.6. Completar el modelo de atención veterinaria

El PDF menciona las historias clínicas y el control de vacunas, pero no especifica completamente su estructura. Para abarcar mejor el dominio, consideraría incorporar:

- Turno: fecha, hora, duración, profesional y estado. Debe impedirse la superposición de turnos médicos.
    
- Vacuna: catálogo de vacunas, dosis aplicadas, fecha, lote y próxima fecha prevista.
    
- Tratamiento: indicaciones, medicación, dosis, frecuencia, duración y evolución.
    
- Diagnóstico: problema identificado, observaciones y vínculo con la consulta.
    
- Internación: admisión, evolución, controles y alta, si el equipo implementa el proceso opcional.
    
- Notificación: recordatorios de vacunas, controles y resultados disponibles, si se implementa el proceso opcional.
    

En particular, una vacuna no debería representarse solamente mediante un atributo de la mascota: conviene registrar cada aplicación como un hecho histórico independiente.

### 4.7. Separar los conceptos de análisis, determinación y resultado

Un estudio de laboratorio puede producir varios valores, por ejemplo, diferentes parámetros de un análisis sanguíneo. Por eso, según el nivel de detalle elegido, podría ser necesario modelar:

- `TipoAnalisis`: define qué estudio se solicita.
    
- `AnalisisLaboratorio`: representa la ejecución concreta de ese estudio.
    
- `Determinacion`: identifica cada parámetro medido.
    
- `Resultado`: contiene el valor obtenido, unidad, rango de referencia y observaciones.
    

Esta separación evita mezclar el catálogo de estudios con las ejecuciones realizadas a pacientes concretos.

Los rangos de referencia también pueden variar según la especie y otras características clínicas, por lo que no deberían considerarse universales.

### 4.8. Evitar duplicación y pérdida de información

El modelo debe garantizar que una muestra pueda rastrearse sin ambigüedad hasta su origen y destino.

Recomiendo:

- Utilizar identificadores únicos para muestras, órdenes, remitos y precintos.
    
- Evitar que una misma muestra quede vinculada accidentalmente a dos mascotas.
    
- Conservar los registros históricos aunque un cliente o una mascota dejen de estar activos.
    
- Definir qué ocurre cuando se anula una orden o un remito.
    
- Registrar fechas y horas de forma consistente.
    
- Diferenciar una eliminación de datos de una anulación lógica o una corrección.
    
- Proteger los datos personales de los clientes y los datos clínicos de las mascotas mediante permisos y controles de acceso.
    

## 5. Reglas de negocio que conviene definir explícitamente

Además de las validaciones escritas en el PDF, propondría documentar las siguientes reglas para evitar contradicciones en la implementación.

| Se puede implementar                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| __Identificación del paciente__<br><br>No se puede registrar una consulta para una mascota inexistente o sin responsable asociado.                           |
| __Coherencia de la derivación__<br><br>Toda muestra debe vincularse con una orden válida, la mascota correspondiente y la consulta que justifica el estudio. |
| __Integridad del envío__<br><br>El remito debe identificar las muestras efectivamente incluidas y el precinto utilizado en ese envío.                        |
| __Recepción controlada__<br><br>Una muestra no puede pasar a procesamiento si fue rechazada por la integridad del precinto.                                  |
| __Transiciones válidas__<br><br>Cada entidad debe permitir únicamente las transiciones de estado definidas para su ciclo de vida.                            |
| __Trazabilidad completa__<br><br>Los cambios críticos deben registrar responsable, fecha y hora, motivo y objeto afectado, sin borrar los eventos previos.   |

## 6. Reportes que se desprenden del dominio

La consigna solicita al menos cuatro reportes no triviales. Para que resulten útiles, no deberían limitarse a contar registros, sino relacionar entidades y aplicar filtros o cálculos.

|Reporte|Información que debería obtener|
|---|---|
|Atenciones y derivaciones por clínica|Cantidad de consultas, órdenes y muestras derivadas en un período, agrupadas por clínica.|
|Muestras rechazadas por fallas de transporte|Cantidad, motivos, transportista, clínica de origen y porcentaje de rechazo sobre el total enviado.|
|Vacunas pendientes y tratamientos|Mascotas con vacunas vencidas o próximas a vencer y tratamientos que requieren seguimiento.|
|Facturación por clínica y laboratorio|Importes por servicio, período, clínica, análisis y estado de pago.|
|Tiempos de tránsito y procesamiento|Tiempo entre despacho y recepción, y entre recepción y finalización del análisis.|

Los dos últimos reportes de trazabilidad permiten evaluar la calidad logística del servicio, no solamente la actividad médica.

## 7. Aplicación de patrones de diseño

Como el PDF exige utilizar al menos dos patrones, conviene elegirlos según los problemas concretos del dominio.

- State (Estado): para modelar el ciclo de vida de la muestra y controlar qué operaciones son válidas en cada estado. Por ejemplo, una muestra rechazada no puede comenzar un análisis.
    
- Observer (Observador): para notificar a otros componentes cuando ocurre un evento relevante, como la disponibilidad de un resultado o un cambio en el estado del envío.
    
- Strategy (Estrategia): para encapsular reglas de viabilidad y conservación diferentes según el tipo de muestra o análisis.
    
- Factory Method (Método Fábrica): podría utilizarse para crear tipos concretos de análisis o de muestra cuando existen variantes con comportamientos distintos.
    

Los dos primeros constituyen una combinación inicial razonable: `State` ayuda a mantener las reglas del ciclo de vida y `Observer` permite desacoplar los cambios de estado de las notificaciones y otras acciones secundarias. No es necesario implementar todos los patrones; conviene justificar los elegidos y evitar agregarlos cuando no resuelven un problema real.

## Conclusión

El dominio debe construirse alrededor de dos grandes áreas relacionadas:

1. Atención clínica: clientes, mascotas, historias clínicas, consultas, profesionales, vacunas y tratamientos.
    
2. Derivación y laboratorio: órdenes, muestras, contenedores, precintos, remitos, transporte, recepción, análisis y resultados.
    

La relación entre ambas áreas se establece principalmente mediante la consulta médica, la orden de derivación y la muestra biológica.

Mi recomendación es priorizar el modelado de la muestra, su historial inmutable de estados, el remito y el control del precinto. Son los elementos que concentran las reglas más críticas del enunciado y los que más condicionarán la calidad del diseño orientado a objetos. Después, se pueden completar los procesos clínicos, la facturación, la agenda y los reportes, manteniendo una separación clara entre las responsabilidades de cada entidad.
[[division_dominio_veterinario]]