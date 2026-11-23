# Entrega E2 · Observatorio veterinario de Colima

Equipo: José Miguel Castellanos · Leonardo Rodríguez García · Etiqueta: `e2` · Tablero: _https://tdl-observatorio-colima.streamlit.app_

## Resumen en tres líneas

Integramos como fuente especializada el directorio geoespacial de unidades económicas de INEGI (DENUE) con GeoPandas y visualización cartográfica interactiva en el tablero público, garantizando cero datos personales.
Establecimos linaje y trazabilidad completa fila a fila en toda la Capa Oro hacia su origen en Capa Bronce y su marca de tiempo de ingesta original.
Formalizamos la Declaración de Ética y Legalidad (`docs/etica-datos.md`), evaluando el marco normativo LFPDPPP/LSNIEG, términos de uso de APIs, análisis de `robots.txt` y mitigación de sesgos.

---

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Fuente especializada (45) | [`extractores/denue.py`](../../extractores/denue.py), [`data/plata/denue_colima.geojson`](../../data/plata/denue_colima.geojson), [`tablero/app.py`](../../tablero/app.py) | Directorio geoespacial de clínicas veterinarias, farmacias y estéticas de mascotas en Colima (SCIAN 541941, 541942, 461121, 812110). Modelado con GeoPandas (EPSG:4326), validado en puerta de calidad espacial y visible en mapa interactivo del tablero. **Cero datos personales:** sanitización estricta de nombres físicos y teléfonos antes de persistir en Bronce. |
| Declaración de ética y legalidad (30) | [`docs/etica-datos.md`](../etica-datos.md) | Análisis exhaustivo por fuente (INEGI BISE, Banxico SIE, INEGI DENUE, OSM). Incluye bases legales (LSNIEG, LFPDPPP, LFDA), términos de servicio, análisis técnico de `robots.txt`, licencias de uso (CC BY 4.0), protocolos de extracción ética (User-Agent, rate limit $\ge 1.5$ s, retroceso exponencial) y diagnóstico de 4 sesgos con sus mitigaciones. |
| Linaje de datos (15) | [`data/oro/`](../../data/oro/), [`docs/linaje-datos.md`](../linaje-datos.md), [`tests/test_linaje.py`](../../tests/test_linaje.py) | Cada registro de toda la Capa Oro (`usd_mxn_mensual.csv`, `vet_ingresos_mensual.csv`, `denue_colima_geo.csv`) porta explícitamente `archivo_bronce_origen`, `fecha_ingesta` (UTC) e identificador de `fuente_origen`. Respaldado por el diccionario de datos y verificado al 100 % por pruebas automáticas. |

---

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Diseño y principios (25) | [Propuesta §3 E2](../E0/propuesta.md#e2--experimento-factorial-ruta-negocio), [`laboratorio/`](../../laboratorio/) | Experimento factorial $2^3$ en ruta negocio (Mensaje: precio vs beneficio $\times$ Imagen: mascota sola vs con veterinario $\times$ Horario: 09:00 vs 20:00). 16 corridas aleatorizadas con 2 réplicas por tratamiento y bloqueo semanal para controlar fluctuaciones exógenas de demanda. |
| Dos factores con interacción (20) | [`laboratorio/`](../../laboratorio/) | Modelo ANOVA de dos vías con interacción ($Y_{ijk} = \mu + \alpha_i + \beta_j + (\alpha\beta)_{ij} + \epsilon_{ijk}$) interpretando si la efectividad del mensaje promocional depende significativamente del tipo de imagen seleccionada. |
| Completo vs. fraccionado (20) | [`laboratorio/`](../../laboratorio/) | Matriz comparativa entre un diseño $2^4$ completo (16 corridas) y un fraccionado $2^{4-1}$ (8 corridas, resolución IV con generador $I = ABCD$). Identificación de alias principales donde los efectos principales quedan libres de confusión con interacciones dobles ($A = BCD$), logrando 50 % de ahorro en corridas. |
| Análisis y confirmación (25) | [`laboratorio/salidas/`](../../laboratorio/salidas/) | Cálculo de efectos principales, gráficas de interacción, validación de supuestos de normalidad y homocedasticidad en residuos, concluyendo con la combinación óptima verificada en corrida de confirmación. |

---

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Evaluación ISO/IEC 25010 (30) | [`docs/plan-sqa.md`](../plan-sqa.md), [`calidad/fiabilidad.csv`](../../calidad/fiabilidad.csv) | Evaluación de las 8 características del producto: adecuación funcional (100 % requerimientos verificados), eficiencia de desempeño (pipeline $< 3$ s), compatibilidad (GeoJSON estándar EPSG:4326), usabilidad, fiabilidad (disponibilidad 100 % medida en bitácora tras 9 días), seguridad (0 secretos con gitleaks, 0 vulnerabilidades con pip-audit), mantenibilidad (cobertura pruebas $> 75$ %) y portabilidad. |
| Evaluación ISO/IEC 25012 (25) | [`data/oro/diccionario_oro.csv`](../../data/oro/diccionario_oro.csv), [`data/cuarentena/`](../../data/cuarentena/) | Evaluación de calidad sobre los datos de Capa Oro: exactitud sintáctica y semántica (validación por rangos y BBox), completitud (100 % en campos obligatorios), consistencia (formato ISO 8601 y claves únicas), credibilidad (fuentes oficiales INEGI/Banxico) y actualidad (bitácora continua de captura). |
| Antecedentes normativos (10) | [`docs/plan-sqa.md`](../plan-sqa.md) | Cuadro comparativo que vincula la transición de ISO/IEC 9126 a la suite ISO/IEC 25000 (SQuaRE) con el enfoque de gestión de calidad basado en procesos de ISO 9001:2015. |
| Auditoría cruzada (25) | [`docs/`](../) | Reporte de auditoría externa aplicado al observatorio del equipo asignado en su entrega E1, estructurando hallazgos clasificados por severidad (crítico, mayor, menor), evidencias objetivas y recomendaciones de acción correctiva. |

---

## Relatoría de etapa

[`docs/relatoria-E2.md`](../relatoria-E2.md)

---

## Issues de la entrega anterior

No se recibieron issues pendientes de E1 por parte del cuerpo docente; el panel de medio término validó satisfactoriamente el avance del observatorio y autorizó la continuidad a E2.
