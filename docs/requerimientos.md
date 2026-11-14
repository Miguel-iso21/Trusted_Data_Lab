# Requerimientos verificables · Observatorio veterinario de Colima

Cada requerimiento fue revisado contra cuatro características: **necesario** (si se quita, el
observatorio pierde algo que el cliente necesita), **no ambiguo** (una sola lectura), **verificable**
(tiene una prueba objetiva) y **rastreable** (se liga a un archivo o prueba concreta).

| ID | Requerimiento | Cómo se comprueba | Rastreo |
|---|---|---|---|
| RF-01 | El sistema captura el tipo de cambio FIX de Banxico (serie SF43718) al menos una vez al día sin intervención humana. | La bitácora tiene una fila `banxico-sie` por cada día del periodo. | `.github/workflows/captura.yml`, `calidad/bitacora_capturas.csv` |
| RF-02 | El sistema captura el índice de ingresos de servicios veterinarios para mascotas de INEGI (indicador 716898) en cada ejecución programada. | La bitácora tiene una fila `inegi-bise` por ejecución. | `extractores/inegi.py` |
| RF-03 | La serie histórica de ingresos veterinarios tiene al menos 36 periodos mensuales. | `data/oro/vet_ingresos_mensual.csv` tiene ≥ 36 filas (hoy: 224, de 2008-01 a 2026-08). | `pipeline/oro.py` |
| RF-04 | Todo registro guardado en bronce incluye fuente, URL de origen y fecha-hora UTC de captura. | Las columnas `fuente`, `url_origen` y `capturado_en` no tienen nulos. | `tests/test_extractores.py` |
| RF-05 | Un registro con fecha fuera del formato `YYYY-MM-DD`, valor nulo o valor fuera de rango (Banxico 5–50 MXN, INEGI 10–500) no llega a plata y se guarda en cuarentena con su motivo. | Prueba con registros inválidos conocidos: los 3 llegan a cuarentena con un motivo no vacío. | `tests/test_pipeline.py::test_puerta_manda_a_cuarentena_con_motivo` |
| RF-06 | Si una misma fecha se captura varias veces, plata conserva solo la captura más reciente. | En plata no hay pares (`serie`, `fecha`) repetidos. | `pipeline/limpieza.py` |
| RF-07 | Los atípicos se marcan (columna `atipico_iqr`) y no se eliminan. | El número de filas antes y después de marcar es el mismo. | `tests/test_pipeline.py::test_atipicos_se_marcan_no_se_borran` |
| RF-08 | La capa oro excluye el mes en curso del promedio mensual del dólar. | Prueba con fecha de corte simulada. | `tests/test_pipeline.py::test_oro_mensual_excluye_mes_en_curso` |
| RF-09 | La capa oro tiene un diccionario de datos con tabla, columna, tipo, descripción y origen de cada columna. | Cada columna de los CSV de oro aparece en `diccionario_oro.csv`. | `data/oro/diccionario_oro.csv` |
| RF-10 | El pronóstico se elige por el menor error en los últimos 12 meses (datos que el modelo no vio) y se publica con intervalo de predicción al 95 %. | `comparacion_modelos.csv` tiene MAE, RMSE y MAPE de 4 modelos; `pronostico.csv` tiene `inferior_95` y `superior_95`. | `laboratorio/pronostico.py` |
| RNF-01 | Disponibilidad de la captura ≥ 95 % medida en los últimos 14 días. | `python -m pipeline.fiabilidad` → columna `disponibilidad`. | `calidad/fiabilidad.csv` |
| RNF-02 | La tasa de rechazo de la puerta de calidad es ≤ 5 % por fuente. | `python -m pipeline.run` termina con código 0. | `pipeline/run.py` |
| RNF-03 | La cobertura de pruebas es ≥ 60 %. | `pytest --cov --cov-fail-under=60` pasa en CI. | `.github/workflows/ci.yml` |
| RNF-04 | Ningún token aparece en el código, los datos o el historial de git. | `gitleaks` en CI sin hallazgos; prueba de que el token de INEGI no se escribe. | `tests/test_extractores.py::test_inegi_main_no_escribe_el_token` |
| RNF-05 | El extractor respeta `robots.txt`, se identifica con un User-Agent con contacto y espera ≥ 1 s entre peticiones al mismo dominio. | Pruebas de `ExtractorEtico`; la pausa por defecto es 1.5 s. | `extractores/base.py`, `tests/test_extractores.py` |
| RNF-06 | Un tercero puede clonar el repositorio y reproducir oro y el pronóstico con los comandos del README. | Clonado limpio + `pip install -r requirements.txt` + `python -m pipeline.run` + `python -m laboratorio.pronostico`. | `README.md` |

**Requerimientos que reescribimos tras la revisión** (ejemplos de ambigüedad corregida):

- "El sistema debe ser confiable" → no verificable. Se convirtió en RNF-01 y RNF-02, con número.
- "Los datos deben estar limpios" → ambiguo. Se convirtió en RF-05, RF-06 y RF-07, con reglas concretas.
