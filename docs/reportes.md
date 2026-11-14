# 📊 Sistema de Reportes y Analítica de Gestión — Patitas & Co.

Documento técnico y conceptual del módulo de **Reportes y Analítica de Gestión** para la cátedra de **Desarrollo de Aplicaciones con Objetos (DAO)**. Aquí se detallan los 4 reportes no triviales diseñados para el sistema, explicando **qué hace cada uno, cómo se calculan sus métricas, qué clases/entidades intervienen y cómo defenderlos conceptualmente**.

---

## 🎯 ¿Qué hace que estos reportes sean "No Triviales"?

En ingeniería de software y programación orientada a objetos, un reporte es **no trivial** cuando:
1. **Navega entre múltiples entidades del modelo:** No es un volcado plano de una sola tabla, sino un cruce estructurado entre diferentes agregados (`Paciente` ➔ `Consulta` ➔ `Orden` ➔ `Muestra` ➔ `Envio` ➔ `Recepcion` ➔ `Resultado`).
2. **Calcula métricas agregadas en tiempo de ejecución:** Las variables (promedios, diferencias de tiempo, porcentajes, ratios de cumplimiento) no existen guardadas estáticamente; se computan al momento de la solicitud.
3. **Aplica reglas de negocio del dominio:** Evalúa compromisos de nivel de servicio (SLA), rangos seguros de temperatura y reglas de bioseguridad del patrón *State*.

---

## ⏱️ Reporte 1: Tiempo Promedio de Tránsito y Cumplimiento de SLA Analítico (IMPLEMENTADO)

### 1. ¿Qué hace este reporte?
Monitorea de punta a punta la eficiencia logística y analítica de la red. Mide cuánto tarda una muestra desde que sale despachada en la clínica periférica, cuándo arriba al Laboratorio Central de Derivación, y cuánto demora el laboratorio en procesar la muestra y emitir el informe final validado. Además, compara el tiempo total contra la **matriz de SLA (Service Level Agreement)** comprometida con el veterinario y el tutor.

### 2. Clases y entidades involucradas
| Entidad / Clase | Dónde está la información | Atributos clave utilizados |
| :--- | :--- | :--- |
| `Envio` / `Remito` | Backend (`app.models.envio`) | `fecha_despacho`, `transportista`, `remito.numero` |
| `Muestra` | Backend (`app.models.orden_analisis`) | `codigo_etiqueta`, `estado`, `fecha_extraccion` |
| `TipoAnalisis` | Backend (`app.models.orden_analisis`) | `nombre`, `descripcion` |
| `OrdenAnalisis` | Backend (`app.models.orden_analisis`) | `prioridad` (`Normal` vs `Urgente`), `consulta.pet`, `veterinario` |
| `RecepcionEnvio` | Backend (`app.models.recepcion`) | `fecha_recepcion`, `muestras_recibidas` |
| `ResultadoAnalisis` | Backend (`app.models.recepcion`) | `fecha_recepcion` (fecha informe), `estado` |

### 3. Fórmulas y algoritmo de cálculo

1. **Tiempo de Tránsito Logístico ($t_{\text{transito}}$):**
   $$t_{\text{transito}} = \text{Fecha/Hora Recepción en Lab} - \text{Fecha/Hora Despacho en Clínica}$$
   *(Medido en horas con precisión decimal)*.

2. **Tiempo de Procesamiento Analítico ($t_{\text{proceso}}$):**
   $$t_{\text{proceso}} = \text{Fecha/Hora Emisión Resultado} - \text{Fecha/Hora Recepción en Lab}$$

3. **Tiempo Total de Ciclo o Turnaround Time ($TAT$):**
   $$TAT = t_{\text{transito}} + t_{\text{proceso}} = \text{Fecha/Hora Resultado} - \text{Fecha/Hora Despacho}$$

4. **Verificación de Cumplimiento de SLA:**
   Se busca el SLA objetivo según el tipo de análisis y prioridad médica:
   * **Hemograma Completo:** Normal: $24.0\,\text{hs}$ \| Urgente: $12.0\,\text{hs}$
   * **Perfil Bioquímico Hepático:** Normal: $24.0\,\text{hs}$ \| Urgente: $12.0\,\text{hs}$
   * **Perfil Renal (Urea y Creatinina):** Normal: $24.0\,\text{hs}$ \| Urgente: $12.0\,\text{hs}$
   * **Orina Completa y Sedimento:** Normal: $24.0\,\text{hs}$ \| Urgente: $12.0\,\text{hs}$
   * **Coproparasitológico Seriado:** Normal: $48.0\,\text{hs}$ \| Urgente: $24.0\,\text{hs}$
   * **Citología Cutánea / PAAF:** Normal: $48.0\,\text{hs}$ \| Urgente: $24.0\,\text{hs}$
   * **Dosaje Hormonal (T4 / Cortisol):** Normal: $72.0\,\text{hs}$ \| Urgente: $36.0\,\text{hs}$

   *Condición:*
   $$\text{Cumple SLA} = \begin{cases} \text{Verdadero (A Tiempo)}, & \text{si } TAT \le SLA_{\text{objetivo}} \\ \text{Falso (Demorado)}, & \text{si } TAT > SLA_{\text{objetivo}} \end{cases}$$
   $$\text{Diferencia SLA} = TAT - SLA_{\text{objetivo}}$$

5. **Tasa Global de Cumplimiento (% SLA):**
   $$\text{Tasa Cumplimiento} = \left( \frac{\text{Cantidad de Muestras que Cumplen SLA}}{\text{Total de Muestras Analizadas}} \right) \times 100$$

6. **Puntualidad por Transportista:**
   Se computa el tiempo medio de viaje por transportista y se considera viaje en tiempo óptimo si $t_{\text{transito}} \le 6.0\,\text{hs}$.
   $$\text{Puntualidad Transportista} = \left( \frac{\text{Viajes } \le 6.0\,\text{hs}}{\text{Total de Viajes del Transportista}} \right) \times 100$$

### 4. Funcionalidades implementadas
* **Identidad y branding oficial:** Integración del logotipo oficial de Patitas & Co. en los 3 canales de salida (Excel, PDF y Correo electrónico).
* **Interfaz interactiva:** Tableros de KPIs, gráfico de barras comparativas (Tránsito vs Proceso vs SLA Línea), ranking de transportistas y tabla detallada con buscador en vivo.
* **Filtros multidimensionales:** Por rango de fechas (`Desde` / `Hasta`), por `Tipo de Análisis`, por `Transportista` y por `Prioridad` (`Normal`/`Urgente`).
* **Descarga en Excel (.xlsx):** Generación binaria nativa con `openpyxl` que incluye el logotipo incrustado en la celda `A1`, cabeceras en verde `#2D5864` y formato condicional (verde para muestras a tiempo, rojo para demoradas).
* **Descarga en PDF oficial:** Generación con `reportlab` en orientación apaisada (*landscape*), encabezado institucional con logo a la izquierda, tablas estilizadas y nota de bioseguridad.
* **Envío automático por Correo:** Integración con servidor SMTP de Gmail (`STARTTLS` puerto 587) para despachar un resumen HTML con cabecera gráfica que muestra el logo mediante Content-ID (`cid:logo_patitas`) y adjuntos PDF/Excel.

### 5. Endpoints de la API
* `GET /api/v1/reportes/tiempos-sla`: Retorna el JSON con KPIs, agrupaciones y detalles.
* `GET /api/v1/reportes/tiempos-sla/excel`: Genera y descarga el archivo `.xlsx`.
* `GET /api/v1/reportes/tiempos-sla/pdf`: Genera y descarga el documento `.pdf`.
* `POST /api/v1/reportes/tiempos-sla/enviar-email`: Despacha el correo electrónico con adjuntos.

---

## 🛡️ Reporte 2: Muestras Biológicas Rechazadas por Fallas en el Transporte y Bioseguridad (IMPLEMENTADO)

### 1. ¿Qué hace este reporte?
Audita exhaustivamente la calidad sanitaria y la cadena de custodia biológica de las muestras remitidas al Laboratorio Central. Monitorea cuántas muestras debieron ser descartadas/rechazadas al momento de la recepción física y realiza un **análisis de causa raíz** cruzando:
* **Integridad de precintos numerados:** Identificación de precintos rotos, violentados o con códigos discordantes frente al remito original (`PREC-XXXXX`).
* **Cadena de frío y control termométrico:** Detección de **excursiones térmicas** fuera del rango bioseguro ($2.0^\circ\text{C}$ a $8.0^\circ\text{C}$) registradas por los sensores de las conservadoras térmicas.
* **Incidentes de bioseguridad:** Tubos fisurados, hemólisis severa, volumen insuficiente o inconsistencias documentales sin resolución.
* **Índice de confiabilidad de la flota de transportistas:** Evaluación del desempeño y siniestralidad de cada chofer o empresa de logística.

---

### 2. Clases y entidades involucradas
| Entidad / Clase | Módulo / Ubicación | Atributos clave utilizados |
| :--- | :--- | :--- |
| `Muestra` | Backend (`app.models.orden_analisis`) | `codigo_etiqueta`, `estado` (`rechazada`, `aceptada`), `orden` |
| `Envio` | Backend (`app.models.envio`) | `transportista`, `fecha_despacho`, `remito_id`, `registros_temperatura` |
| `Remito` | Backend (`app.models.envio`) | `numero`, `fecha_emision` |
| `RegistroTemperatura` | Backend (`app.models.envio`) | `temperatura_medida_c`, `fecha_registro` (termometría salida/llegada) |
| `VerificacionPrecinto` | Backend (`app.models.recepcion`) | `codigo_esperado`, `codigo_observado`, `estado` (`Integro`, `Roto`, `Ausente`) |
| `Incidencia` | Backend (`app.models.recepcion`) | `tipo`, `descripcion`, `resolucion`, `muestra_id` |
| `OrdenAnalisis` / `Pet` / `Responsible` | Backend (`app.models.orden_analisis`, `app.models.consulta`) | `paciente.name`, `species`, `responsible.full_name`, `tipo_analisis.nombre` |

---

### 3. Fórmulas y algoritmos de cálculo

1. **Tasa de Rechazo Global ($TR$):**
   $$TR = \left( \frac{\text{Cantidad de Muestras Rechazadas}}{\text{Total de Muestras Auditadas}} \right) \times 100$$
   *(Meta de bioseguridad: $TR \le 5.0\%$)*.

2. **Tasa de Conformidad de Muestras ($TC$):**
   $$TC = 100\% - TR = \left( \frac{\text{Cantidad de Muestras Aceptadas}}{\text{Total de Muestras Auditadas}} \right) \times 100$$

3. **Índice de Integridad de Precintos ($IP$):**
   $$IP = \left( \frac{\text{Precintos Íntegros y Coincidentes}}{\text{Total de Muestras Auditadas}} \right) \times 100$$

4. **Conformidad de Cadena de Frío ($CCF$):**
   $$CCF = \left( \frac{\text{Muestras con } 2.0^\circ\text{C} \le T_{\text{llegada}} \le 8.0^\circ\text{C}}{\text{Total de Muestras Auditadas}} \right) \times 100$$

5. **Distribución y Frecuencia de Causas Raíz ($FC_i$):**
   Para cada causa $i$ (Rotura de Precinto, Excursión Térmica, Hemólisis, etc.):
   $$FC_i = \left( \frac{\text{Conteo de Rechazos por Causa } i}{\text{Total de Muestras Rechazadas}} \right) \times 100$$
   * **Severidad Crítica:** Rotura o violación de precinto, código discordante o excursión térmica $> 8.0^\circ\text{C}$.
   * **Severidad Moderada:** Muestra insuficiente, rotulación ilegible o hemólisis leve.

6. **Confiabilidad y Calificación por Transportista ($CT$):**
   Para cada chofer o empresa de transporte $k$:
   $$CT_k = \left( \frac{\text{Muestras Conformes bajo custodia de } k}{\text{Total de Muestras Transportadas por } k} \right) \times 100$$
   * **Excelente:** $CT_k \ge 95.0\%$
   * **Aceptable:** $80.0\% \le CT_k < 95.0\%$
   * **Crítico:** $CT_k < 80.0\%$

---

### 4. Funcionalidades implementadas
* **Identidad y branding oficial:** Integración del logotipo oficial de Patitas & Co. en los 3 formatos (Excel con celda `A1`, PDF apaisado y Correo HTML con `cid:logo_patitas`).
* **Tablero de Control de Bioseguridad en Frontend:**
  * 6 tarjetas KPI interactivas con codificación visual de colores según umbrales de seguridad.
  * Gráfico 1: Barras horizontales de distribución porcentual por Causa Raíz con etiquetas de severidad (*Crítica* vs *Moderada*).
  * Gráfico 2: Panel de confiabilidad por transportista con barras de progreso de conformidad y motivo de falla más frecuente.
  * Tabla de trazabilidad y auditoría de precintos (con comparador de códigos esperado vs observado, rangos termométricos y acciones correctivas).
* **Filtros multidimensionales:** Por `Causa de Rechazo`, por `Transportista`, por `Estado de Muestra` (`Todas` / `Rechazada` / `Aceptada`), y por rango de fechas (`Desde` / `Hasta`).
* **Descarga en Excel (.xlsx):** Libro multihistorial con formato profesional en verdes `#2D5864` / `#5F8E9C`, hoja de métricas agregadas y hoja de registro detallado de muestras con resaltado condicional.
* **Descarga en PDF oficial:** Documento apaisado (*landscape*) con encabezado corporativo, matriz de KPIs de bioseguridad, causas de rechazo y log de incidentes para auditorías regulatorias de SENASA.
* **Envío automático por Correo Electrónico:** Integración directa con servidor SMTP (Gmail) enviando un correo con diseño HTML corporativo, KPIs destacados, logo incrustado y adjuntos en PDF y Excel.

---

### 5. Endpoints de la API
* `GET /api/v1/reportes/muestras-rechazadas`: Devuelve la estructura JSON completa con KPIs, distribución causal, confiabilidad de transporte y muestras auditadas.
* `GET /api/v1/reportes/muestras-rechazadas/excel`: Genera y descarga el libro de auditoría `.xlsx`.
* `GET /api/v1/reportes/muestras-rechazadas/pdf`: Genera y descarga el acta de inspección `.pdf`.
* `POST /api/v1/reportes/muestras-rechazadas/enviar-email`: Realiza el despacho SMTP con adjuntos según los filtros seleccionados.

---

---

## 🩺 Reporte 3: Rendimiento Clínico y Tasa de Derivación Médica (IMPLEMENTADO)

### 1. ¿Qué hace este reporte?
Analiza integralmente la actividad médica de la red veterinaria. Cruza la agenda de turnos asignados con las consultas clínicas efectivas y las órdenes de laboratorio prescriptas por cada profesional. 
Permite a la dirección médica:
1. Auditar el **ausentismo** de tutores y pacientes para optimizar la agenda.
2. Evaluar el **perfil prescriptivo** de cada médico veterinario (si su conducta diagnóstica es de *Alta Derivación*, *Moderada* o *Clínico Conservador*).
3. Determinar el **Top de Estudios Prescriptos** a la red central de laboratorio (Hemograma, Bioquímica, Perfil Renal, Citologías, etc.).
4. Asegurar la trazabilidad diagnóstica correlacionando motivo de consulta, diagnóstico presuntivo y determinaciones solicitadas.

### 2. Clases y entidades involucradas
| Entidad / Clase | Dónde está la información | Atributos clave utilizados |
| :--- | :--- | :--- |
| `Turno` | Backend (`app.models.paciente`) | `scheduled_at`, `status` (`atendido`, `ausente`, `cancelado`), `veterinarian_id`, `pet_id`, `reason` |
| `Consulta` | Backend (`app.models.paciente`) | `attended_at`, `reason`, `diagnosis`, `treatment`, `appointment_id`, `veterinarian_id` |
| `Veterinario` | Backend (`app.models.paciente`) | `full_name`, `license_number` (matrícula), `specialty` |
| `Mascota` / `Responsable` | Backend (`app.models.paciente`) | `pet.name`, `pet.species`, `responsible.full_name` |
| `OrdenAnalisis` | Backend (`app.models.orden_analisis`) | `consulta_id`, `veterinario_id`, `detalles.tipo_analisis` |
| `TipoAnalisis` | Backend (`app.models.orden_analisis`) | `nombre`, `descripcion` |

### 3. Fórmulas y algoritmo de cálculo

1. **Tasa de Ausentismo de Pacientes:**
   $$\text{Tasa Ausentismo} = \left( \frac{\text{Turnos Ausentes}}{\text{Total Turnos Agendados}} \right) \times 100$$

2. **Tasa de Asistencia Efectiva:**
   $$\text{Tasa Asistencia} = \left( \frac{\text{Turnos Atendidos}}{\text{Total Turnos Agendados}} \right) \times 100$$

3. **Tasa de Derivación Médica Global y por Profesional:**
   $$\text{Tasa Derivación} = \left( \frac{\text{Consultas con Prescripción de Laboratorio}}{\text{Total Consultas Atendidas}} \right) \times 100$$

4. **Promedio de Determinaciones por Orden:**
   $$\text{Promedio Estudios/Orden} = \frac{\text{Total Determinaciones Solicitadas}}{\text{Total Órdenes Emitidas}}$$

5. **Clasificación del Perfil Prescriptivo:**
   - **Alta Derivación:** $\ge 60\%$ de consultas atendidas derivan en solicitud de análisis complementarios.
   - **Derivación Moderada:** Entre $30\%$ y $60\%$.
   - **Clínico Conservador:** $< 30\%$.

### 4. Endpoints de la API
* `GET /api/v1/reportes/rendimiento-clinico`: Devuelve el JSON analítico con KPIs, ranking por médico, top de estudios, desglose de estados y listado filtrable.
* `GET /api/v1/reportes/rendimiento-clinico/excel`: Genera y descarga el libro Excel `.xlsx` oficial con dos hojas y logo corporativo.
* `GET /api/v1/reportes/rendimiento-clinico/pdf`: Genera y descarga el acta médica `.pdf` apaisada con tablas de auditoría y logo institucional.
* `POST /api/v1/reportes/rendimiento-clinico/enviar-email`: Realiza el despacho SMTP con adjuntos según los filtros seleccionados.

---

## 🔬 Reporte 4: Eficacia Diagnóstica y Hallazgos Críticos (IMPLEMENTADO)

### 1. ¿Qué hace este reporte?
Evalúa la correlación entre la presunción diagnóstica del médico veterinario y los resultados analíticos cuantitativos emitidos por el laboratorio. 
Permite:
1. **Medir la tasa de positividad diagnóstica:** Qué porcentaje de estudios confirman patologías mediante analitos cuantitativos fuera del rango de referencia (`alerta: 'Alto'` o `'Bajo'`).
2. **Evaluar la certeza y concordancia diagnóstica:** Confirmación del diagnóstico presuntivo emitido en consulta versus los hallazgos patológicos objetivos.
3. **Mapeo epidemiológico por especie:** Identificación de perfiles patológicos predominantes según cualquier especie animal admitida por el centro (Caninos, Felinos, Equinos, Conejos / Pequeños mamíferos, Aves, etc.).
4. **Distribución por grupo etario:** Segmentación de patologías en Cachorros/Jóvenes (< 1 año), Adultos (1 a 7 años) y Geriátricos (> 7 años).
5. **Top de analitos críticos:** Ranking de frecuencia y tendencia de parámetros alterados (Glóbulos blancos, Creatinina sérica, ALT/GPT, Glucemia, Lactato sérico, Cristales en orina, etc.).

### 2. Clases y entidades involucradas
| Entidad / Clase | Dónde está la información | Atributos clave utilizados |
| :--- | :--- | :--- |
| `ResultadoAnalisis` | Backend (`app.models.recepcion`) | `datos['valores']` (`parametro`, `valor`, `alerta`, `rangoReferencia`), `conclusionDiagnostica`, `fecha_recepcion` |
| `OrdenAnalisis` / `DetalleOrden` | Backend (`app.models.orden_analisis`) | `consulta_id`, `veterinario`, `detalles.tipo_analisis.nombre` |
| `Mascota` | Backend (`app.models.paciente`) | `name`, `species` (`Canino`, `Felino`, `Equino`, `Conejo`, `Ave`, etc.), `breed`, `birth_date` (cálculo de grupo etario) |
| `Responsable` | Backend (`app.models.paciente`) | `full_name` (tutor a cargo) |
| `Consulta` | Backend (`app.models.paciente`) | `diagnosis` (diagnóstico presuntivo), `reason` (motivo de consulta), `attended_at` |

### 3. Fórmulas de cálculo y algoritmos
1. **Tasa de Positividad Diagnóstica Global:**
   $$\text{Positividad} = \left( \frac{\text{Estudios con Analitos Fuera de Rango (Alto / Bajo)}}{\text{Total Estudios Procesados}} \right) \times 100$$

2. **Índice de Concordancia Diagnóstica:**
   $$\text{Concordancia} = \left( \frac{\text{Estudios donde el Laboratorio Confirma la Presunción Clínica}}{\text{Total Estudios Procesados}} \right) \times 100$$

3. **Positividad Específica por Especie:**
   $$\text{Positividad Especie } k = \left( \frac{\text{Estudios Patológicos en Especie } k}{\text{Total Estudios en Especie } k} \right) \times 100$$

4. **Clasificación por Severidad:**
   - **Crítico:** Desviación severa en glóbulos blancos, creatinina $> 2.5\,\text{mg/dL}$, glucemia descompensada o T4 libre $> 50\,\text{pmol/L}$.
   - **Moderado:** Desviaciones moderadas (hematuria, bacteriuria, aumento leve de enzimas o parásitos).
   - **Fisiológico Normal:** Todos los analitos dentro del intervalo de referencia biológico.

### 4. Endpoints de la API
* `GET /api/v1/reportes/eficacia-diagnostica`: Retorna el JSON analítico con KPIs, desglose por especie, grupo etario, analitos críticos y casos clínicos.
* `GET /api/v1/reportes/eficacia-diagnostica/excel`: Descarga el libro `.xlsx` con dos hojas, formato condicional y logo oficial.
* `GET /api/v1/reportes/eficacia-diagnostica/pdf`: Descarga el informe epidemiológico en `.pdf` landscape con tablas de auditoría.
* `POST /api/v1/reportes/eficacia-diagnostica/enviar-email`: Realiza el despacho SMTP con adjuntos según los filtros seleccionados.

---

## 🏛️ Arquitectura Modular del Subsistema de Reportes

Para mantener el código mantenible, desacoplado y evitar archivos monolíticos, el sistema aplica los principios **SOLID** y el patrón estructural **Facade**:

### Frontend (`vet_front/src/components/modules/reportes/`)
* [ModuloReportes.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/ModuloReportes.tsx): Contenedor orquestador liviano (~110 líneas) responsable de la barra de navegación de pestañas.
* [types.ts](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/types.ts): Definiciones TypeScript comunes e interfaces de datos de los 4 reportes.
* `common/`: Componentes transversales reutilizables para garantizar consistencia visual y no duplicar código:
  * [ReporteHeaderBanner.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/common/ReporteHeaderBanner.tsx): Encabezado oficial con logo institucional y títulos limpios.
  * [KpiCard.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/common/KpiCard.tsx): Tarjeta métrica estandarizada con iconos, valores, subtextos y estilos.
  * [ReporteAccionesBar.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/common/ReporteAccionesBar.tsx): Barra de botones estandarizada (Descargar Excel, PDF, Enviar por Correo, Recargar).
  * [ModalEnvioCorreo.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/common/ModalEnvioCorreo.tsx): Modal unificado de envío SMTP con gestión de adjuntos y validaciones.
* [ReporteTiemposSla.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/ReporteTiemposSla.tsx): Componente autónomo para el Reporte 1 (tiempos de tránsito, SLA, gráficos y exportaciones).
* [ReporteMuestrasRechazadas.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/ReporteMuestrasRechazadas.tsx): Componente autónomo para el Reporte 2 (bioseguridad, rechazos, causas raíz y auditoría).
* [ReporteRendimientoClinico.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/ReporteRendimientoClinico.tsx): Componente autónomo para el Reporte 3 (rendimiento médico, ausentismo, derivaciones y prescripciones).
* [ReporteEficaciaDiagnostica.tsx](file:///d:/Cati/Veterinaria_DAO/vet_front/src/components/modules/reportes/ReporteEficaciaDiagnostica.tsx): Componente autónomo para el Reporte 4 (eficacia diagnóstica, positividad analítica, epidemiología canina/felina y analitos críticos).

### Backend (`vet_back/app/services/reportes/`)
* [reportes_service.py](file:///d:/Cati/Veterinaria_DAO/vet_back/app/services/reportes_service.py): **Fachada unificada (`ReportesService`)** que expone una interfaz limpia a los endpoints y tests, delegando la lógica en los servicios especializados.
* [base.py](file:///d:/Cati/Veterinaria_DAO/vet_back/app/services/reportes/base.py): Constantes compartidas (ej. resolución de ruta del logo institucional `logo-patitas.png`).
* [servicio_tiempos_sla.py](file:///d:/Cati/Veterinaria_DAO/vet_back/app/services/reportes/servicio_tiempos_sla.py): Servicio especializado para el Reporte 1 (SLA, turnaround time, openpyxl, reportlab, correo).
* [servicio_muestras_rechazadas.py](file:///d:/Cati/Veterinaria_DAO/vet_back/app/services/reportes/servicio_muestras_rechazadas.py): Servicio especializado para el Reporte 2 (auditoría sanitaria, cadena de frío, precintos, openpyxl, reportlab, correo).
* [servicio_rendimiento_clinico.py](file:///d:/Cati/Veterinaria_DAO/vet_back/app/services/reportes/servicio_rendimiento_clinico.py): Servicio especializado para el Reporte 3 (rendimiento médico, turnos vs consultas, derivaciones, openpyxl, reportlab, correo).
* [servicio_eficacia_diagnostica.py](file:///d:/Cati/Veterinaria_DAO/vet_back/app/services/reportes/servicio_eficacia_diagnostica.py): Servicio especializado para el Reporte 4 (eficacia diagnóstica, positividad, correlación presuntiva, epidemiología por especie/edad, openpyxl, reportlab, correo).


