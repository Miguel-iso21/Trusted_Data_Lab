# Entrega E1 · Observatorio veterinario de Colima

Equipo: José Miguel Castellanos · Leonardo Rodríguez García · Etiqueta: `e1` · Tablero: _pendiente_

## Resumen en tres líneas

Capturamos dos fuentes oficiales: el índice de ingresos de servicios veterinarios para mascotas de
INEGI (224 meses) y el dólar FIX de Banxico (1,729 días). Las pasamos de bronce a oro con una puerta
de calidad pandera y cuarentena. Pronosticamos 6 meses de ingresos veterinarios con el modelo de
menor error en datos no vistos y montamos CI con pruebas, gitleaks y pip-audit, más un plan SQA IEEE 730.

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Valores faltantes (15) | [`pipeline/limpieza.py`](../../pipeline/limpieza.py) | Los faltantes (`N/E` de Banxico) van a cuarentena con su motivo. **Pendiente:** el diagnóstico MCAR/MAR/MNAR por escrito. |
| Atípicos y ruido (15) | [`marcar_atipicos_iqr`](../../pipeline/limpieza.py) | IQR k = 1.5; se marcan, no se borran (prueba `test_atipicos_se_marcan_no_se_borran`). |
| Normalización, discretización y reducción (15) | [`pipeline/oro.py`](../../pipeline/oro.py), [diccionario](../../data/oro/diccionario_oro.csv) | z-score y min-max en ambas series; terciles bajo/medio/alto; reducción diario → mensual: 1,729 → 82 filas (−95 %). |
| Integración de fuentes (20) | [`data/oro/`](../../data/oro/) | Las dos fuentes quedan en grano mensual (`mes` = YYYY-MM-01). Duplicados por fecha resueltos con la captura más reciente. |
| Puerta de calidad (25) | [`pipeline/limpieza.py`](../../pipeline/limpieza.py), [`data/cuarentena/`](../../data/cuarentena/) | Pandera: formato de fecha, serie no nula, rango por fuente. Rechazo hoy: 0 de 1,729 y 0 de 224. Falla la CI si se rechaza más de 5 %. |

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Caracterización y descomposición (15) | [`descomposicion.png`](../../laboratorio/salidas/descomposicion.png) | Descomposición multiplicativa con periodo 12. |
| Estacionariedad y autocorrelación (15) | [`dickey_fuller.csv`](../../laboratorio/salidas/dickey_fuller.csv), [`acf_pacf.png`](../../laboratorio/salidas/acf_pacf.png) | ADF: p = 0.79 en nivel y p = 0.00002 con una diferencia → d = 1. |
| Cuatro modelos (25) | [`laboratorio/pronostico.py`](../../laboratorio/pronostico.py) | SES, Holt, Holt-Winters y ARIMA(2,1,0); el orden de ARIMA se eligió por AIC. |
| Selección por error (20) | [`comparacion_modelos.csv`](../../laboratorio/salidas/comparacion_modelos.csv) | Prueba con los últimos 12 meses. Gana SES: MAE 16.31, RMSE 16.64, MAPE 13.4 %. |
| Residuos y comunicación (15) | [`residuos.csv`](../../laboratorio/salidas/residuos.csv), [`pronostico.csv`](../../laboratorio/salidas/pronostico.csv) | Pronóstico con IC 95 % (sep-2026: 125.6, entre 107.6 y 143.6). **Ljung-Box no se aprueba** (p = 0.00003); se publica con advertencia. |

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Fiabilidad y disponibilidad (25) | [`docs/fiabilidad-E1.md`](../fiabilidad-E1.md), [`pipeline/fiabilidad.py`](../../pipeline/fiabilidad.py) | MTBF, MTTR y A calculados por script desde la bitácora. **Solo hay 3 ejecuciones del 13-nov**, no 7 días; lo explicamos y no inventamos cifras. |
| Seguridad (15) | [`docs/fiabilidad-E1.md` §3](../fiabilidad-E1.md) | gitleaks y pip-audit sin hallazgos en la CI; tokens solo como secrets; bronce respaldado en git. |
| Requerimientos (10) | [`docs/requerimientos.md`](../requerimientos.md) | 10 funcionales y 6 no funcionales, cada uno con su comprobación y su rastreo. |
| Plan SQA (25) | [`docs/plan-sqa.md`](../plan-sqa.md) | Estructura IEEE 730 con 5 objetivos de calidad medibles. |
| Integración continua (15) | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) | ruff + pytest (cobertura ≥ 60 %) + puerta de datos + pip-audit + gitleaks en cada push. |
| Registros PSP | [`calidad/`](../../calidad/) | Registro de defectos y de tiempo, uno por integrante. |

## Relatoría de etapa

[`docs/relatoria-E1.md`](../relatoria-E1.md)

## Issues de la entrega anterior

Ninguno recibido.
