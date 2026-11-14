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

## 🛡️ Reporte 2: Muestras Biológicas Rechazadas por Fallas en el Transporte (PRÓXIMAMENTE)

### 1. ¿Qué hace este reporte?
Audita la calidad sanitaria y la cadena de custodia biológica. Identifica cuántas muestras debieron ser descartadas/rechazadas al llegar al laboratorio y analiza la causa raíz:
* Rotura o violación del precinto sanitario (`PREC-XXXXX`).
* Excursiones térmicas (quiebre de cadena de frío fuera de $2^\circ\text{C}$ a $8^\circ\text{C}$).
* Muestra insuficiente o tubo deteriorado.

### 2. Clases involucradas
* `MuestraBiologica`: `estadoActual` (`Rechazada`), `tipoMaterial`, `condicionConservacion`.
* `PrecintoSanitario`: `estadoVerificacion` (`Roto`, `Ausente`, `CodigoNoCoincide`).
* `RemitoBiologico`: `temperaturaDespachoC`, `transportista`, `conservadoraId`.
* `Incidencia`: `tipo`, `descripcion`, `remitoId`.

### 3. Fórmulas de cálculo
* **Tasa de Rechazo Global:**
  $$\text{Tasa Rechazo} = \left( \frac{\text{Muestras Rechazadas}}{\text{Total de Muestras Despachadas}} \right) \times 100$$
* **Índice de Confiabilidad por Transportista:**
  $$\text{Confiabilidad} = 100 - \left( \frac{\text{Muestras Rechazadas bajo su custodia}}{\text{Total Muestras que transportó}} \times 100 \right)$$

---

## 🩺 Reporte 3: Rendimiento Clínico y Tasa de Derivación Médica (PRÓXIMAMENTE)

### 1. ¿Qué hace este reporte?
Analiza la actividad médica de la clínica veterinaria. Cruza la agenda de turnos con las consultas efectivas y las órdenes de laboratorio emitidas por cada profesional.

### 2. Clases involucradas
* `Turno`: `veterinario`, `fecha`, `estado` (`Atendido`, `Cancelado`, `Ausente`).
* `ConsultaMedica`: `veterinario`, `requiereAnalisis`, `diagnosticoPresuntivo`.
* `OrdenAnalisis`: `veterinarioSolicitante`, `detalles.tipoAnalisis`.

### 3. Fórmulas de cálculo
* **Tasa de Ausentismo (No-show):**
  $$\text{Ausentismo} = \left( \frac{\text{Turnos Ausentes}}{\text{Total Turnos Agendados}} \right) \times 100$$
* **Tasa de Derivación a Laboratorio por Médico:**
  $$\text{Derivación} = \left( \frac{\text{Consultas con Solicitud de Laboratorio}}{\text{Total Consultas Atendidas}} \right) \times 100$$
* **Ranking de Estudios más Prescriptos por Profesional:** Conteo agrupado de `tipoAnalisis`.

---

## 🔬 Reporte 4: Eficacia Diagnóstica y Hallazgos Críticos (PRÓXIMAMENTE)

### 1. ¿Qué hace este reporte?
Evalúa la correlación entre la presunción diagnóstica del médico y los resultados analíticos cuantitativos. Mide qué porcentaje de los estudios confirman patologías mediante valores anormales (`alerta: 'Alto'` o `'Bajo'`) discriminados por especie y edad de la mascota.

### 2. Clases involucradas
* `ResultadoAnalisis`: `valores` (`parametro`, `valor`, `rangoReferencia`, `alerta`), `conclusionDiagnostica`.
* `OrdenAnalisis`: `mascotaId`, `consultaId`.
* `Mascota`: `especie` (`Canino` vs `Felino`), `fechaNacimientoAprox` (edad).
* `ConsultaMedica`: `diagnosticoPresuntivo`.

### 3. Fórmulas de cálculo
* **Tasa de Positividad Diagnóstica:**
  $$\text{Positividad} = \left( \frac{\text{Análisis con Alertas Patológicas (Alto/Bajo)}}{\text{Total Análisis Procesados}} \right) \times 100$$
* **Frecuencia de Patología por Especie:** Agrupamiento de parámetros alterados según especie (ej: Uremia/Creatinina elevada en felinos geriátricos).

