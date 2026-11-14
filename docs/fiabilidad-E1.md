# Fiabilidad, disponibilidad y seguridad · E1

## 1. Cómo se mide

Cada ejecución de un extractor (manual o programada) escribe una fila en
[`calidad/bitacora_capturas.csv`](../calidad/bitacora_capturas.csv) con la hora UTC, la fuente,
el estado (`ok` o `falla`), las filas capturadas, la duración y el error. Las métricas salen de
esa bitácora con un script, no se escriben a mano:

```bash
python -m pipeline.fiabilidad      # genera calidad/fiabilidad.csv
```

| Métrica | Definición usada |
|---|---|
| Tasa de éxito | ejecuciones `ok` / ejecuciones totales |
| MTTR | promedio del tiempo entre una falla y la siguiente ejecución `ok` de la misma fuente |
| MTBF | (periodo observado − tiempo caído) / número de fallas |
| Disponibilidad | A = MTBF / (MTBF + MTTR) |

El cálculo tiene pruebas automáticas con bitácoras sintéticas de resultado conocido
([`tests/test_fiabilidad.py`](../tests/test_fiabilidad.py)).

## 2. Resultado al 13 de noviembre de 2026

| Fuente | Ejecuciones | Fallas | Tasa de éxito | MTTR | MTBF | Disponibilidad |
|---|---|---|---|---|---|---|
| banxico-sie | 2 | 1 | 50 % | 34 s | 0 h | 0 % |
| inegi-bise | 1 | 0 | 100 % | — | — | 100 % |

**Lectura honesta:** estos números **no son todavía una medición de fiabilidad**. La bitácora
empezó el 13 de noviembre a las 18:03 (hora de Colima) y solo tiene 3 ejecuciones del mismo día,
todas manuales. La rúbrica pide 7 días de bitácora y no los tenemos, porque la captura programada
no corrió desde el 6 de noviembre: el repositorio se publicó en GitHub hasta el 13 de noviembre.
No vamos a presentar como medido algo que no medimos.

- La falla de Banxico (18:03:55) fue un `400 Bad Request`. La misma consulta respondió bien
  34 segundos después (18:04:29). La causa no está confirmada. Como el reintento la resolvió sin
  cambiar el código, la tratamos como falla del servicio o del token, no como defecto del extractor.
- Con una sola falla en 34 segundos de observación, el MTBF y la disponibilidad no tienen sentido
  estadístico. Comparados contra el objetivo **OC-1 (≥ 95 %)** del [plan SQA](plan-sqa.md),
  **el objetivo no se puede evaluar todavía**.

**Plan:** la captura diaria (08:00 de Colima, `.github/workflows/captura.yml`) queda activa
desde el 13 de noviembre. El mismo script dará la medición de 7 días el 20 de noviembre y la de
14 días, que pide el Sello TDL, el 27 de noviembre.

## 3. Seguridad del sistema de información

| Control | Herramienta | Resultado | Evidencia |
|---|---|---|---|
| Secretos en todo el historial de git | gitleaks (CI, `fetch-depth: 0`) | Sin hallazgos | Actions → Integracion continua #2 |
| Vulnerabilidades de dependencias | pip-audit (CI) | Sin hallazgos | Actions → Integracion continua #2 |
| Tokens fuera del código | Variables de entorno / GitHub *secrets* | Ningún token en el repo | `extractores/*.py`, prueba `test_inegi_main_no_escribe_el_token` |
| Token oculto en errores y en datos | La URL de INEGI se guarda como `<TOKEN>` | Verificado por prueba | `tests/test_extractores.py` |
| Mínimo permiso | `ci.yml`: `contents: read`; solo `captura.yml` tiene `contents: write` | Aplicado | `.github/workflows/` |
| Respaldo de la capa bronce | Bronce versionado en git y respaldado en GitHub | Restauración = `git clone` | Historial del repo |

**Confidencialidad, integridad y disponibilidad:**
- *Confidencialidad:* el proyecto no captura datos personales (son índices y tipos de cambio
  agregados). Los tokens se guardan como *secrets*.
- *Integridad:* bronce no se sobrescribe, cada captura es un archivo nuevo con fecha. La puerta de
  calidad no deja pasar valores fuera de rango.
- *Disponibilidad:* se mide en la sección 2. Las dos fuentes corren de forma independiente: si una
  falla, la otra se sigue capturando.
