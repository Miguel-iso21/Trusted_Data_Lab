# Plan de Aseguramiento de Calidad del Software (SQA)
**Observatorio veterinario de Colima · Trusted Data Lab** · Estructura basada en IEEE 730

Versión 1.0 · 13 de noviembre de 2026 · Equipo: José Miguel Castellanos, Leonardo Rodríguez García

---

## 1. Propósito y alcance

Este plan define cómo aseguramos que el observatorio entregue cifras confiables. Cubre:

- **Software:** extractores (`extractores/`), pipeline bronce → plata → oro (`pipeline/`),
  laboratorio de pronóstico (`laboratorio/`) y tablero (`tablero/`).
- **Datos:** las capas bronce, plata, oro y cuarentena de `data/`.
- **Proceso:** captura programada, integración continua, revisiones y registro de defectos y tiempo.

Fuera del alcance: la infraestructura de GitHub y la exactitud de origen de las fuentes oficiales
(INEGI y Banxico). Para estas últimas solo verificamos que lo recibido sea consistente.

**Aseguramiento vs. control.** El *aseguramiento* (este plan) previene defectos con procesos:
revisiones, CI y puertas de calidad. El *control* detecta defectos en el producto ya hecho:
pruebas y validación de datos. Hacemos las dos cosas.

## 2. Roles y responsabilidades

| Rol | Persona | Responsabilidades de calidad |
|---|---|---|
| Data Engineer | José Miguel Castellanos | Extractores, puerta de calidad, CI, bitácora de captura |
| Data Statistician | Leonardo Rodríguez García | Supuestos estadísticos (puerta 3), validez de los pronósticos |
| Quality Lead (rota en cada entrega) | E1: Leonardo · E2: José Miguel · E3: Leonardo | Revisa el trabajo del otro con la lista de comprobación (§6) |

**Independencia del revisor:** nadie aprueba su propio trabajo. El Quality Lead de cada entrega es
quien *no* hizo la mayor parte de esa parte.

## 3. Estándares y métricas

**Estándares que seguimos:**

- Código: PEP 8, verificado con `ruff` (reglas E, F, W, I, B, UP, BLE y S de seguridad).
- Datos: esquema pandera por fuente (fecha `YYYY-MM-DD`, serie no nula, valor en rango).
- Proceso: PSP (registro individual de defectos con los 10 tipos de PSP y registro de tiempo).
- Producto y datos: ISO/IEC 25010 e ISO/IEC 25012 (evaluación en E2).

**Objetivos de calidad medibles:**

| # | Objetivo | Meta | Cómo se mide | Dónde |
|---|---|---|---|---|
| OC-1 | Disponibilidad de la captura | ≥ 95 % | `python -m pipeline.fiabilidad` sobre la bitácora | `calidad/fiabilidad.csv` |
| OC-2 | Tasa de rechazo de la puerta de calidad | ≤ 5 % | `pipeline/run.py` termina con error si se supera | Log de Actions |
| OC-3 | Cobertura de pruebas automáticas | ≥ 60 % | `pytest --cov --cov-fail-under=60` en CI | Log de Actions |
| OC-4 | Secretos expuestos en el repositorio | 0 | `gitleaks` en CI sobre todo el historial | Log de Actions |
| OC-5 | Vulnerabilidades conocidas en dependencias | 0 abiertas | `pip-audit` en CI | Log de Actions |

## 4. Revisiones y auditorías

| Revisión | Cuándo | Quién | Evidencia |
|---|---|---|---|
| Revisión de código con lista de comprobación | Antes de cada entrega | Quality Lead | Defectos encontrados en `calidad/defectos-*.csv`, fase `revision` |
| Revisión de supuestos estadísticos | Antes de publicar un hallazgo | Data Statistician | `laboratorio/salidas/` (ADF, Ljung-Box) |
| Revisión de issues de los docentes | En cada entrega | Ambos | Issues cerrados con commit |
| Auditoría cruzada (externa) | 19 al 23 de noviembre | Otro equipo | Reporte de auditoría en `docs/` (E2) |

## 5. Pruebas

- **Unitarias y de integración** (`tests/`, `pytest`). Extractores con respuestas HTTP simuladas
  (sin red), puerta de calidad, capa oro, flujo bronce → oro de punta a punta en carpetas
  temporales y cálculo de fiabilidad.
- **Puerta 1, validación de datos** (`pipeline/limpieza.py`). Todo registro que no cumple el esquema
  va a `data/cuarentena/` con su motivo. Nada se borra en silencio.
- **Puerta 2, integración continua** (`.github/workflows/ci.yml`). En cada push corre linter, pruebas
  con cobertura mínima, puerta de datos, `pip-audit` y `gitleaks`. Si algo falla, el cambio no se integra.
- **Puerta 3, supuestos estadísticos** (`laboratorio/pronostico.py`). Dickey-Fuller antes de modelar
  y Ljung-Box sobre los residuos del modelo ganador. Si un supuesto falla, el hallazgo se publica con
  la advertencia o con un método que no dependa de él.

## 6. Reporte de problemas y acciones correctivas

1. Quien encuentra un defecto lo registra en **su** archivo `calidad/defectos-<nombre>.csv`: número,
   fecha, tipo PSP, fase en que se introdujo, fase en que se eliminó, minutos de corrección,
   defecto de origen y descripción.
2. Si el defecto lo reporta un docente o el auditor, se abre un *issue* en GitHub con la etiqueta
   de la materia (`ing-datos`, `estadistica`, `calidad`) y se cierra con el commit que lo corrige.
3. Las fallas de captura quedan solas en `calidad/bitacora_capturas.csv`. Una falla que dura más de
   24 h se registra también como defecto.
4. **Acción correctiva:** cada defecto de tipo `datos` o `sistema` debe dejar una prueba automática
   que lo habría detectado.

**Lista de comprobación del Quality Lead:**

- [ ] ¿Hay alguna prueba nueva para cada función nueva?
- [ ] ¿Algún token, contraseña o correo personal escrito en el código o en los datos?
- [ ] ¿Las rutas usan `pipeline/config.py` y no rutas absolutas de una computadora?
- [ ] ¿Los rechazos de datos llevan motivo?
- [ ] ¿El extractor respeta `robots.txt`, se identifica y hace pausa entre peticiones?
- [ ] ¿Cada cifra del tablero o de la relatoría se puede regenerar con un comando del README?

## 7. Herramientas

| Propósito | Herramienta |
|---|---|
| Linter y análisis estático | ruff |
| Pruebas y cobertura | pytest, pytest-cov |
| Validación de datos | pandera |
| Secretos | gitleaks |
| Vulnerabilidades | pip-audit |
| Automatización | GitHub Actions (`captura.yml` y `ci.yml`) |
| Fiabilidad | `pipeline/fiabilidad.py` |

## 8. Control de versiones y configuración

- Todo vive en GitHub (`Miguel-iso21/Trusted_Data_Lab`), en la rama `main`.
- Cada entrega se marca con su etiqueta (`e0` … `e4`) antes de las 23:59 del día de entrega.
- Las dependencias van fijadas por versión exacta en `requirements.txt` para que el análisis sea reproducible.
- Los tokens (`BANXICO_TOKEN`, `INEGI_TOKEN`) solo existen como *secrets* de GitHub o variables de
  entorno locales. Nunca se escriben en el código ni en los datos: la URL de INEGI se guarda con `<TOKEN>`.
- **Respaldo de la capa bronce:** bronce se versiona en git, así que cada captura queda respaldada en
  GitHub con su historial. Para restaurarla basta clonar el repositorio.

## 9. Riesgos

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Una API cambia su formato o deja de responder | Media | Alto | Parser con pruebas, bitácora de fallas y reintentos con espera exponencial |
| Token vencido o revocado | Media | Alto | La falla se registra en la bitácora; el token se renueva y se actualiza el secret |
| INEGI revisa cifras ya publicadas | Alta | Medio | Bronce conserva cada captura con fecha; plata usa la más reciente |
| La serie mensual de INEGI se actualiza con ~2 meses de rezago | Alta | Medio | El pronóstico se documenta con su fecha de corte |
| Se filtra un secreto al historial | Baja | Alto | gitleaks en CI; si ocurre, se revoca el token de inmediato |
| Un integrante no puede explicar la parte del otro | Media | Alto | Rotación del Quality Lead y repaso cruzado antes del panel |
