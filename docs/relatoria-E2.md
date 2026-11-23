# Relatoría E2 · Observatorio veterinario de Colima

Equipo: José Miguel Castellanos (Data Engineer) · Leonardo Rodríguez García (Data Statistician)  
Periodo: 17 al 23 de noviembre de 2026

---

## 1. Qué nos propusimos

- Integrar una fuente de datos especializada al observatorio: el Directorio Estadístico Nacional de Unidades Económicas (INEGI DENUE) georreferenciado mediante GeoPandas, con visualización cartográfica en el tablero público y estricta política de cero datos personales (LFPDPPP).
- Garantizar la trazabilidad y el linaje bidireccional completo en la Capa Oro, asegurando que cada registro de todas las tablas analíticas identifique su archivo de origen en Capa Bronce, su proveedor y su fecha-hora UTC de ingesta.
- Formalizar la Declaración de Ética y Legalidad (`docs/etica-datos.md`) evaluando términos de uso, análisis técnico de `robots.txt`, licencias de datos abiertas y protocolos de mitigación de sesgos.

---

## 2. Qué hicimos

Trabajamos ambos integrantes al mismo tiempo en una sola computadora (programación en pareja), por lo que las actividades registradas son idénticas en ambos registros de tiempo (`calidad/tiempo-*.csv`):

| Fecha | Qué | Quién | Horas |
|---|---|---|---|
| 17-nov 10:00–11:30 | Panel de medio término ante los tres docentes; retroalimentación y defensa individual de E0 y E1 | Ambos, en pareja | 1.50 |
| 17-nov 16:00–17:30 | Planeación de E2: selección de fuente especializada geoespacial DENUE y diseño del experimento factorial | Ambos, en pareja | 1.50 |
| 18-nov 15:00–17:00 | Extractor de INEGI DENUE (`extractores/denue.py`), módulo de sanitización de privacidad y bitácora | Ambos, en pareja | 2.00 |
| 19-nov 16:00–17:30 | Puerta de calidad espacial en `pipeline/limpieza.py` (bounding box Colima, municipios) y GeoDataFrame con GeoPandas | Ambos, en pareja | 1.50 |
| 20-nov 15:30–17:00 | Capa Oro geoespacial, cálculo de zonas funcionales, resumen municipal y trazabilidad por fila en todas las tablas de Oro | Ambos, en pareja | 1.50 |
| 21-nov 16:00–18:00 | Redacción formal de la Declaración de Ética y Legalidad (`docs/etica-datos.md`) y Manual de Linaje (`docs/linaje-datos.md`) | Ambos, en pareja | 2.00 |
| 22-nov 15:00–17:00 | Visualización cartográfica interactiva, filtros espaciales y visores de trazabilidad en Streamlit (`tablero/app.py`) | Ambos, en pareja | 2.00 |
| 23-nov 10:00–11:45 | Pruebas unitarias (`tests/test_denue.py`, `tests/test_linaje.py`), corrección del defecto JMC-2 (GDAL) y relatoría E2 | Ambos, en pareja | 1.75 |
| | **Total de la etapa E2 (17 al 23 de noviembre)** | | **13.75 h por persona** |

---

## 3. Qué decidimos y por qué

1. **Selección de la fuente especializada: INEGI DENUE con GeoPandas frente a Redes Sociales o APIs con OAuth.**  
   *Decisión:* Adoptamos el Directorio Estadístico Nacional de Unidades Económicas (DENUE) con GeoPandas para geolocalizar clínicas veterinarias, farmacias y estéticas de mascotas en los 10 municipios de Colima.  
   *Alternativas descartadas:* Se descartó la API de YouTube/Reddit porque introducía métricas de vanidad o discusiones no focalizadas geográficamente en Colima; se descartó OAuth por requerir credenciales con caducidad efímera que amenazaban la reproducibilidad sin intervención humana. DENUE aporta valor geográfico directo a los negocios locales y enlaza de forma natural con el análisis multivariado por AGEB previsto para E3.

2. **Linaje granular por registro frente a metadatos globales en cabecera.**  
   *Decisión:* Inyectamos las columnas `archivo_bronce_origen`, `fecha_ingesta` y `fuente_origen` directamente en cada fila de la Capa Oro (`usd_mxn_mensual.csv`, `vet_ingresos_mensual.csv` y `denue_colima_geo.csv`).  
   *Alternativas descartadas:* Almacenar el linaje en un archivo JSON separado o bitácora global. Se descartó porque al momento de auditar o consultar una fila atípica (por ejemplo, una observación extrema en un mes específico), el auditor tendría que cruzar logs manualmente; con linaje en fila, la procedencia del dato es inmediata y autónoma.

3. **Sanitización de privacidad irreversible en Capa Bronce frente a filtrado en Capa Plata.**  
   *Decisión:* La eliminación de datos de personas físicas (propietarios, teléfonos residenciales, correos personales) se realiza en el extractor (`extractores/denue.py`) antes de que el archivo toque el disco en `data/bronce/`.  
   *Alternativas descartadas:* Filtrar los datos en la etapa de limpieza de Capa Plata. Se descartó en cumplimiento estricto con la LFPDPPP: almacenar datos personales en crudo dentro de un repositorio de control de versiones constituiría un tratamiento y almacenamiento no autorizado, exponiendo el proyecto a riesgos de seguridad y no conformidades legales.

---

## 4. Qué salió mal y cómo lo corregimos

- **Defecto JMC-2 (interfaz / entorno - registrado en `calidad/defectos-jose-miguel-castellanos.csv`):**  
  Al intentar exportar el GeoDataFrame a formato GeoJSON con `gdf.to_file(..., driver="GeoJSON")`, la ejecución fallaba en entornos sin los binarios compilados de C/GDAL (`GDAL DLL could not be found` en `pyogrio`).  
  *Corrección:* Reemplazamos la llamada externa por el método nativo `gdf.to_json()`, escribiendo el GeoJSON mediante las bibliotecas estándar de Python. Se verificó con la suite de pruebas unitarias (`test_denue.py`).
- **Defecto LRG-1 (datos - registrado en `calidad/defectos-leonardo-rodriguez-garcia.csv`):**  
  Para validar la robustez de la Puerta de Calidad geoespacial, inyectamos intencionalmente dos registros de control: uno fuera de los límites estatales de Colima (CDMX) y otro con coordenadas nulas. El validador inicial fallaba al procesar coordenadas nulas lanzando `TypeError`.  
  *Corrección:* Se blindó la función `validar_denue()` con validación defensiva de tipos, asegurando que ambos registros defectuosos terminen en `data/cuarentena/denue_rechazados.csv` con su `motivo_rechazo` explícito, sin interrumpir el pipeline y manteniendo la tasa de rechazo en 4.44 % ($\le 5.0\,\%$).

---

## 5. Qué aprendimos

### Ingeniería de Datos
Comprendimos que la integración de datos geoespaciales impone retos dimensionales que van más allá del análisis tabular clásico. Una coordenada geográfica no es simplemente un par de números flotantes: requiere un Sistema de Referencia de Coordenadas (CRS) estandarizado (EPSG:4326 - WGS84) y validaciones espaciales estrictas (bounding boxes) para evitar que datos erróneos de otras entidades contaminen los análisis locales. Asimismo, aprendimos que la privacidad según la LFPDPPP se diseña desde la arquitectura (Privacy by Design): el mejor dato personal protegido es aquel que nunca se llega a persistir en la Capa Bronce. La trazabilidad fila a fila en la Capa Oro transforma un dataset opaco en una fuente fidedigna y totalmente auditable.

### Análisis Estadístico
Comprendimos la relevancia del diseño experimental multifactorial para pasar de la simple observación pasiva a la intervención causal. Mientras que en E1 modelamos el pronóstico de la demanda con series de tiempo, en E2 la estructuración del experimento $2^3$ permite aislar los efectos principales y las interacciones entre mensaje, imagen y horario, descartando variables confusas mediante aleatorización y réplicas. El análisis comparativo entre un diseño factorial completo ($2^4$) y uno fraccionado ($2^{4-1}$) nos demostró cómo se pueden economizar corridas experimentales a cambio de confundir interacciones de orden superior (alias), principio clave para la optimización de recursos en proyectos de ciencia de datos.

### Calidad en los Sistemas de Información
Aprendimos a aplicar los modelos de calidad formalmente: la norma **ISO/IEC 25010** para la evaluación del producto de software (demostrando adecuación funcional, fiabilidad y mantenibilidad) y la norma **ISO/IEC 25012** para la evaluación de los datos (evaluando exactitud, completitud, consistencia, credibilidad y actualidad sobre la Capa Oro). Entendimos la evolución histórica desde la antigua norma ISO/IEC 9126 hacia la familia ISO/IEC 25000 (SQuaRE), alineada al enfoque de procesos de ISO 9001. La auditoría cruzada nos enseñó a evaluar un observatorio ajeno con criterio objetivo, clasificando hallazgos por severidad (crítico, mayor, menor) y emitiendo recomendaciones constructivas basadas en evidencia.

---

## 6. Evidencias

- **Repositorio oficial:** https://github.com/Miguel-iso21/Trusted_Data_Lab
- **Fuente especializada geoespacial (DENUE):**
  - Extractor: [`extractores/denue.py`](../extractores/denue.py)
  - Capa Bronce: [`data/bronce/denue/`](../data/bronce/denue/)
  - Capa Plata: [`data/plata/denue_colima.csv`](../data/plata/denue_colima.csv), [`data/plata/denue_colima.geojson`](../data/plata/denue_colima.geojson)
  - Capa Oro: [`data/oro/denue_colima_geo.csv`](../data/oro/denue_colima_geo.csv), [`data/oro/denue_resumen_municipal.csv`](../data/oro/denue_resumen_municipal.csv)
  - Cuarentena con motivo de rechazo: [`data/cuarentena/denue_rechazados.csv`](../data/cuarentena/denue_rechazados.csv)
- **Documentación de gobernanza y trazabilidad:**
  - Declaración de Ética y Legalidad: [`docs/etica-datos.md`](etica-datos.md)
  - Manual de Linaje y Trazabilidad: [`docs/linaje-datos.md`](linaje-datos.md)
  - Diccionario de Datos actualizado: [`data/oro/diccionario_oro.csv`](../data/oro/diccionario_oro.csv)
- **Tablero interactivo con cartografía:** [`tablero/app.py`](../tablero/app.py) (pestaña "Mapa geoespacial (DENUE)")
- **Pruebas automáticas y aseguramiento:**
  - 26 pruebas unitarias aprobadas: [`tests/test_denue.py`](../tests/test_denue.py), [`tests/test_linaje.py`](../tests/test_linaje.py)
  - Bitácora de capturas y fiabilidad continua: [`calidad/bitacora_capturas.csv`](../calidad/bitacora_capturas.csv), [`calidad/fiabilidad.csv`](../calidad/fiabilidad.csv)
  - Registros de tiempo y defectos PSP: [`calidad/`](../calidad/)

---

## Uso de IA generativa

Declaramos el uso de asistentes de inteligencia artificial de acuerdo con los lineamientos del proyecto:

- **Herramienta:** Asistente de programación basado en LLM (Claude Code / Antigravity).
- **Para qué se utilizó:**
  1. Estructuración del extractor geoespacial `extractores/denue.py` y del pipeline de conversión GeoJSON sin dependencias binarias pesadas.
  2. Implementación de las pruebas unitarias automatizadas para validación de coordenadas, cuarentena y trazabilidad de linaje.
  3. Redacción inicial y organización de las secciones normativas de `docs/etica-datos.md` y `docs/linaje-datos.md`.
- **Aporte y control del equipo humano:**
  - Definición del sector veterinario de Colima, selección de los códigos SCIAN y diseño de las zonas urbanas de análisis.
  - Validación de las reglas geográficas del bounding box de Colima y diseño de los registros de control para la puerta de calidad.
  - Registro manual y verídico de los tiempos de trabajo y defectos en los formatos PSP.
  - Revisión exhaustiva de todo el código generado, ejecución de pruebas locales y capacidad total de defensa técnica en el Demo Day.
