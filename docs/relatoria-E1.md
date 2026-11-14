# Relatoría E1 · Observatorio veterinario de Colima

Equipo: José Miguel Castellanos (Data Engineer) · Leonardo Rodríguez García (Data Statistician)
Periodo: 2 al 13 de noviembre de 2026

## 1. Qué nos propusimos

- Llevar las dos fuentes (INEGI y Banxico) de bronce a oro sin intervención manual, con una puerta
  de calidad que rechace con motivo y una tasa de rechazo ≤ 5 %.
- Pronosticar 6 meses del índice de ingresos de servicios veterinarios para mascotas (INEGI 716898),
  eligiendo entre 4 modelos por su error en los últimos 12 meses.
- Tener integración continua (linter, pruebas ≥ 60 % de cobertura, puerta de datos, gitleaks y
  pip-audit) y un plan SQA adaptado al proyecto.

## 2. Qué hicimos

Trabajamos los dos al mismo tiempo en una sola computadora, así que cada bloque aparece igual en
los dos registros de tiempo (`calidad/tiempo-*.csv`).

| Fecha | Qué | Quién | Horas |
|---|---|---|---|
| 12-nov 15:00–18:00 | Registro y obtención de los tokens de las APIs de Banxico SIE e INEGI BISE | Ambos, en pareja | 3.00 |
| 13-nov 15:00–16:00 | Elección del sector veterinario y de las fuentes INEGI 716898 y Banxico SF43718 | Ambos, en pareja | 1.00 |
| 13-nov 16:00–17:00 | Extractor ético base, extractores de Banxico e INEGI y bitácora de capturas | Ambos, en pareja | 1.00 |
| 13-nov 17:00–18:00 | Pipeline bronce → plata (pandera + cuarentena) → oro (normalización, terciles, diccionario) | Ambos, en pareja | 1.00 |
| 13-nov 18:00–18:32 | Captura histórica (1,729 días de dólar 2020–2026 y 224 meses de ingresos veterinarios 2008-01 a 2026-08), laboratorio de pronóstico (descomposición, ADF, ACF/PACF, SES, Holt, Holt-Winters y ARIMA), pruebas y flujos de captura e integración continua | Ambos, en pareja | 0.53 |
| 13-nov 18:32–18:45 | Repositorio git, README y publicación en GitHub | Ambos, en pareja | 0.22 |
| 13-nov 18:45–18:52 | Corrección de la CI (defecto JMC-1) | Ambos, en pareja | 0.12 |
| 13-nov 18:52–18:58 | Medición de fiabilidad, plan SQA, requerimientos, relatoría y ficha de entrega | Ambos, en pareja | 0.10 |
| 13-nov 18:58–19:05 | Tablero Streamlit; 21 pruebas automáticas (89 % de cobertura) | Ambos, en pareja | 0.12 |
| 13-nov 19:05–19:15 | Secrets y permisos de Actions, primera captura automática en GitHub | Ambos, en pareja | 0.17 |
| | **Total de la etapa (12 y 13 de noviembre)** | | **7.25 h por persona** |

## 3. Qué decidimos y por qué

1. **Serie a pronosticar: ingresos veterinarios de INEGI, no precios de veterinarias locales.**
   No existe una fuente pública de precios de consultas en Colima con 36 periodos de historia.
   El índice mensual de INEGI tiene 224 periodos. *Descartado:* hacer scraping de sitios de
   veterinarias, porque no tienen historial y casi ninguna publica precios.
2. **Cuarentena en vez de borrar.** Todo registro rechazado se guarda con su motivo en
   `data/cuarentena/`. Los atípicos se *marcan* con IQR (`atipico_iqr`) y no se eliminan, porque un
   salto en ingresos puede ser el hallazgo. *Descartado:* filtrar en silencio dentro del pandas.
3. **Elegir el modelo por error en datos no vistos.** Separamos los últimos 12 meses como prueba.
   Ganó el suavizamiento exponencial simple (RMSE 16.64, MAPE 13.4 %) frente a ARIMA(2,1,0), Holt
   y Holt-Winters. *Descartado:* quedarnos con ARIMA por tener el menor AIC (1534.5), porque el
   AIC mide el ajuste dentro de la muestra y no el pronóstico.

## 4. Qué salió mal y cómo lo corregimos

- **Defecto JMC-1 (entorno):** la primera ejecución de la CI en GitHub falló porque `pytest` no
  encontraba los paquetes del proyecto. Localmente pasaba porque lo corríamos con `python -m pytest`.
  Se corrigió agregando `pythonpath` en `pyproject.toml` (commit `b9de1a1`); la CI #2 pasó.
  Lección: correr las pruebas exactamente como las corre la CI.
- **Captura programada tardía:** el repositorio se publicó hasta el 13 de noviembre, así que no
  tenemos los 7 días de bitácora que pide la medición de fiabilidad (ver `docs/fiabilidad-E1.md`).
  Acción: captura diaria activa desde el 13 de noviembre; la medición de 7 días sale el 20 de noviembre.
- **El modelo ganador no pasa Ljung-Box** (p = 0.00003): sus residuos tienen autocorrelación, lo que
  indica que queda estructura sin modelar. Lo publicamos con esa advertencia (puerta 3) y lo
  revisaremos con SARIMA o con un tramo posterior a 2020.
- **Falla de Banxico** (`400 Bad Request`) en la primera captura; el reintento a los 34 s funcionó.
  Queda en la bitácora como dato de fiabilidad.

## 5. Qué aprendimos

### Ingeniería de Datos
Aprendimos que limpiar no es lo mismo que borrar. Banxico marca con `N/E` los días sin dato; si
los hubiéramos eliminado con un `dropna()`, nadie sabría cuántos se perdieron ni por qué. Por eso
la puerta de calidad manda cada registro rechazado a `data/cuarentena/` con su motivo, y los
atípicos solo se marcan (`atipico_iqr`): un salto en los ingresos puede ser el hallazgo, no un
error. También vimos que toda reducción tiene un costo. Al agregar el dólar de diario a mensual
pasamos de 1,729 filas a 82 (−95 %), lo que nos permite compararlo con la serie mensual de INEGI,
pero perdemos la volatilidad dentro del mes. Si en E2 o E3 nos importa un brinco del dólar en una
semana, tendremos que volver a la capa plata, que conserva el dato diario.

### Análisis Estadístico
Aprendimos que el modelo más sofisticado no es necesariamente el mejor. Con la prueba de
Dickey-Fuller vimos que el índice de ingresos veterinarios no es estacionario (p = 0.79) y que lo
es con una diferencia (p = 0.00002), por eso usamos d = 1 en ARIMA. El ARIMA(2,1,0) tuvo el menor
AIC (1534.5), pero al probar los cuatro modelos en los últimos 12 meses, que no habían visto,
ganó el suavizamiento exponencial simple, con un error medio de 16.3 puntos (MAPE 13.4 %). El AIC
mide qué tan bien se ajusta el modelo a lo que ya conoce; el error en datos de prueba mide qué tan
bien pronostica, que es lo que le importa al cliente. Y aun el modelo ganador falla Ljung-Box
(p = 0.00003): sus errores siguen un patrón, así que queda información sin aprovechar. Un
pronóstico sin revisar sus residuos puede verse bien en la gráfica y estar mal planteado.

### Calidad en los Sistemas de Información
Aprendimos la diferencia entre asegurar y controlar la calidad. Las pruebas y la puerta de datos
son *control*: encuentran defectos en lo que ya hicimos. El plan SQA y la integración continua son
*aseguramiento*: hacen que el defecto no llegue a `main`. Lo vimos con el defecto JMC-1: las
pruebas pasaban en nuestra computadora y fallaron en GitHub porque se ejecutaban de otra forma.
Sin la CI no nos habríamos dado cuenta. También aprendimos que una métrica sin suficientes datos
engaña. Con 3 ejecuciones el script calculó una disponibilidad de 0 % para Banxico y de 100 % para
INEGI; ninguna de las dos cifras dice algo real. Preferimos reportar que todavía no podemos medir
la fiabilidad a presentar un número que no se sostiene.

## 6. Evidencias

- Repositorio: https://github.com/Miguel-iso21/Trusted_Data_Lab
- Commits: `10fb3c9` (observatorio inicial), `b9de1a1` (corrección de la CI), `b6609b8`
  (plan SQA, requerimientos y fiabilidad), `c1cb078` (primera captura automática), `4b8f432` (tablero)
- Integración continua: pestaña Actions, corrida "Integracion continua #2" en verde
- Pronóstico: `laboratorio/salidas/comparacion_modelos.csv`, `pronostico.png`, `residuos.csv`
- Puerta de calidad: `data/cuarentena/`, `pipeline/limpieza.py`
- Fiabilidad: `calidad/bitacora_capturas.csv`, `calidad/fiabilidad.csv`

## Uso de IA generativa

Usamos **Claude Code**, el asistente de programación de Anthropic, en el editor (VS Code) para:

- **Código:** escribir los extractores, el pipeline bronce → plata → oro, el laboratorio de
  pronóstico, el script de fiabilidad, el tablero y las pruebas automáticas, a partir de lo que
  pide el documento del proyecto.
- **Depuración:** diagnosticar la falla de la CI (defecto JMC-1) reproduciéndola localmente.
- **Documentación:** redactar los borradores del plan SQA, los requerimientos, el reporte de
  fiabilidad, la ficha de entrega y esta relatoría.

Nosotros elegimos el sector y las fuentes, conseguimos los tokens, configuramos GitHub (secrets,
permisos y captura) y aportamos las horas y los datos reales del proceso. Revisamos cada archivo
y podemos explicarlo en la defensa. Lo que la IA no podía saber (cuánto tiempo trabajamos, quién
hizo qué) lo escribimos nosotros, y las cifras salen de los scripts, no de la IA.
