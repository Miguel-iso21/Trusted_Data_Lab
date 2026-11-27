# Entrega E2 · Observatorio veterinario de Colima

Equipo: José Miguel Castellanos · Leonardo Rodríguez García · Etiqueta: `e2` · Tablero: _https://tdl-observatorio-colima.streamlit.app_

## Resumen en tres líneas

Integramos como fuente especializada el directorio geoespacial de unidades económicas de INEGI (DENUE) con GeoPandas y visualización cartográfica interactiva en el tablero público, garantizando cero datos personales.
Establecimos linaje y trazabilidad completa fila a fila en toda la Capa Oro hacia su origen en Capa Bronce y su marca de tiempo de ingesta original.
Corrimos (26-nov, tarde) un experimento factorial 2³ sobre la puerta de calidad: Parquet + pandera es 37 % más rápido que la configuración actual sin perder exactitud.
Formalizamos la Declaración de Ética y Legalidad (`docs/etica-datos.md`), evaluando el marco normativo LFPDPPP/LSNIEG, términos de uso de APIs, análisis de `robots.txt` y mitigación de sesgos.

---

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Fuente especializada (45) | [`extractores/denue.py`](../../extractores/denue.py), [`tests/test_denue.py`](../../tests/test_denue.py), [`tablero/app.py`](../../tablero/app.py) | **Corrección del 27 de noviembre:** los 45 establecimientos que se entregaron como DENUE estaban escritos a mano en el código (una lista de respaldo que se usaba cuando la API fallaba) y no provenían de INEGI. Se eliminaron de todas las capas. El extractor ahora consulta la API oficial del DENUE (método `BuscarAreaAct`, entidad 06, clases SCIAN del observatorio) con `DENUE_TOKEN`, descarta en bronce razón social, teléfono, correo y sitio web, y si la API falla lo registra en la bitácora sin datos de respaldo. Primera captura real el 27-nov: **638 establecimientos de Colima** en los 10 municipios (122 veterinarias, 492 tiendas de mascotas, 22 estéticas/hoteles de mascotas y 2 veterinarios de ganado), 0 rechazos en la puerta. También se corrigió el código SCIAN de estéticas: 812110 son salones de belleza para personas; se usa 812990 filtrado por nombre. |
| Declaración de ética y legalidad (30) | [`docs/etica-datos.md`](../etica-datos.md) | Análisis exhaustivo por fuente (INEGI BISE, Banxico SIE, INEGI DENUE, OSM). Incluye bases legales (LSNIEG, LFPDPPP, LFDA), términos de servicio, análisis técnico de `robots.txt`, licencias de uso (CC BY 4.0), protocolos de extracción ética (User-Agent, rate limit $\ge 1.5$ s, retroceso exponencial) y diagnóstico de 4 sesgos con sus mitigaciones. |
| Linaje de datos (15) | [`data/oro/`](../../data/oro/), [`docs/linaje-datos.md`](../linaje-datos.md), [`tests/test_linaje.py`](../../tests/test_linaje.py) | Cada registro de toda la Capa Oro (`usd_mxn_mensual.csv`, `vet_ingresos_mensual.csv`, `denue_colima_geo.csv`) porta explícitamente `archivo_bronce_origen`, `fecha_ingesta` (UTC) e identificador de `fuente_origen`. Respaldado por el diccionario de datos y verificado al 100 % por pruebas automáticas. |

---

## Análisis Estadístico

> **Corrección del 26 de noviembre:** al etiquetar `e2`, esta sección describía un experimento de
> negocio que no se había corrido. El experimento se corrió el 26-nov por la **ruta de ingeniería**,
> después de la fecha de entrega. Detalle en [`docs/experimento-E2.md`](../experimento-E2.md).

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Diseño y principios (25) | [`laboratorio/experimento.py`](../../laboratorio/experimento.py), [`resultados_2k3.csv`](../../laboratorio/salidas/experimento/resultados_2k3.csv), [`parametros.json`](../../laboratorio/salidas/experimento/parametros.json) | 2³ sobre la puerta de calidad: formato de plata (CSV/Parquet) × motor de validación (fila por fila/pandera) × tamaño (×1/×20). 2 réplicas = 16 corridas, orden aleatorio con semilla guardada y cada réplica como bloque (bloque significativo, p = 0.013). Corre contra una copia local, nunca contra las APIs. |
| Dos factores con interacción (20) | [`resultados_dos_factores.csv`](../../laboratorio/salidas/experimento/resultados_dos_factores.csv), [`anova_dos_factores.csv`](../../laboratorio/salidas/experimento/anova_dos_factores.csv), [`interaccion_dos_factores.png`](../../laboratorio/salidas/experimento/interaccion_dos_factores.png) | Formato (CSV/Parquet/Feather) × tamaño (×1/×10/×50), 3 réplicas = 27 corridas. ANOVA de dos vías: la interacción es significativa (p < 0.0001). Con ×1 los formatos empatan (~7 ms); con ×50 CSV es 6–7 veces más lento. |
| Completo vs. fraccionado (20) | [`matriz_2k4_completo.csv`](../../laboratorio/salidas/experimento/matriz_2k4_completo.csv), [`matriz_2k4-1_fraccionado.csv`](../../laboratorio/salidas/experimento/matriz_2k4-1_fraccionado.csv), [`alias_2k4-1.csv`](../../laboratorio/salidas/experimento/alias_2k4-1.csv) | 2⁴ (16 corridas) contra 2⁴⁻¹ con D = ABC (I = ABCD, resolución IV): 8 corridas, ahorro del 50 %. Alias A = BCD … AB = CD, AC = BD, AD = BC. La fracción confundiría nuestra interacción más fuerte (B × C) con A × D. Matrices verificadas por pruebas. |
| Análisis y confirmación (25) | [`anova_2k3.csv`](../../laboratorio/salidas/experimento/anova_2k3.csv), [`efectos_2k3.csv`](../../laboratorio/salidas/experimento/efectos_2k3.csv), [`supuestos_2k3.png`](../../laboratorio/salidas/experimento/supuestos_2k3.png), [`confirmacion.csv`](../../laboratorio/salidas/experimento/confirmacion.csv) | Sobre log(s): pandera ×0.26 (p = 0.0001), tamaño ×8.0, motor × tamaño significativo; el formato no es significativo con 2 réplicas. Shapiro p = 0.77; Breusch-Pagan p = 0.042, por eso se confirmó con HC3 (mismas conclusiones). Óptimo: Parquet + pandera. Confirmación 5 contra 5: 37 % más rápido que la configuración actual (p = 3 × 10⁻⁷), dentro del intervalo de predicción y con 0 registros mal clasificados. |

---

## Calidad en los Sistemas de Información

> **Corrección del 26 de noviembre:** las cuatro filas de esta sección describían trabajo sin
> evidencia en el repositorio. Quedan marcadas como **pendientes** hasta que exista el archivo.

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Evaluación ISO/IEC 25010 (30) | **Pendiente** | Falta un documento con una métrica medida por característica. Evidencia ya disponible para algunas: fiabilidad ([`calidad/fiabilidad.csv`](../../calidad/fiabilidad.csv), 9 días, 21/22 ejecuciones exitosas), eficiencia de desempeño ([experimento](../experimento-E2.md)), seguridad (gitleaks y pip-audit en CI). |
| Evaluación ISO/IEC 25012 (25) | **Pendiente** | Falta medir exactitud, completitud, consistencia, credibilidad y actualidad sobre la capa oro con un script. |
| Antecedentes normativos (10) | **Pendiente** | Falta el cuadro ISO/IEC 9126 → ISO/IEC 25000 (SQuaRE) → ISO 9001. |
| Auditoría cruzada (25) | **Pendiente** | Falta el reporte de la auditoría que hicimos al equipo asignado y el que recibimos. |

---

## Relatoría de etapa

[`docs/relatoria-E2.md`](../relatoria-E2.md)

---

## Issues de la entrega anterior

No se recibieron issues pendientes de E1 por parte del cuerpo docente; el panel de medio término validó satisfactoriamente el avance del observatorio y autorizó la continuidad a E2.
