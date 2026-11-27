# Experimento factorial E2 · Ruta ingeniería

**Pregunta:** ¿qué configuración de la puerta de calidad (bronce → plata) procesa los datos en menos
tiempo sin dejar de detectar los registros inválidos?

**Respuesta corta:** lo que más pesa es el **motor de validación**. Con pandera (vectorizado), la
puerta tarda alrededor de la cuarta parte que validando fila por fila, y con lotes grandes es unas
11 veces más rápida. El formato de la capa plata casi no importa con lotes chicos. Con lotes
grandes, **Parquet + pandera** fue un **37 % más rápido** que la configuración actual (CSV + pandera)
en la corrida de confirmación, **sin ningún registro mal clasificado**.

Código: [`laboratorio/experimento.py`](../laboratorio/experimento.py) · Datos crudos y gráficas:
[`laboratorio/salidas/experimento/`](../laboratorio/salidas/experimento/) · Pruebas:
[`tests/test_experimento.py`](../tests/test_experimento.py)

```bash
python -m laboratorio.experimento                  # vuelve a medir (los tiempos varían un poco)
python -m laboratorio.experimento --solo-analisis  # recalcula todo desde los CSV guardados: mismos números
```

## 1. Por qué la ruta de ingeniería

La propuesta original era un experimento de negocio con la veterinaria entrevistada: 16 publicaciones
variando mensaje, imagen y horario. No confirmamos el acuerdo a tiempo para correrlo, así que el
26 de noviembre pasamos a la ruta de ingeniería, que el proyecto también contempla. Este experimento
sirve además como evidencia de *eficiencia de desempeño* en la evaluación ISO/IEC 25010 y como base
de la *optimización medida* de E3.

## 2. Diseño 2³

| Factor | Nivel − | Nivel + |
|---|---|---|
| A · Formato de escritura de plata | CSV | Parquet |
| B · Motor de validación (`limpieza.validar`) | Fila por fila (`iterrows`) | Vectorizado (pandera) |
| C · Tamaño del lote | 1,737 registros reales de Banxico (×1) | Replicados ×20 (34,740) |

- **Respuestas:** segundos para validar, escribir plata y cuarentena y volver a leer plata; y número
  de registros **mal clasificados**. A cada lote se le inyecta un 2 % de registros inválidos
  conocidos: un tercio fuera de rango, un tercio sin valor y un tercio con fecha mal formada.
- **Aleatorización:** orden de corrida aleatorio con semilla fija (20261126), guardada en
  `parametros.json`.
- **Réplicas:** 2 por tratamiento → 16 corridas.
- **Bloqueo:** cada réplica es un bloque con su propio orden aleatorio. El bloque resultó
  significativo (p = 0.013): la computadora no estuvo igual de cargada en las dos tandas, y bloquear
  evitó que esa variación se confundiera con los efectos.
- **Ética:** todo corre contra una copia local de `data/bronce/banxico/` en una carpeta temporal.
  Ninguna corrida consulta a Banxico ni a INEGI.
- **Calentamiento:** antes de medir se corre una vez cada configuración sin cronometrar, para que
  las importaciones y la caché no se carguen a la primera corrida.

## 3. Resultados del 2³

Medición del 26 de noviembre de 2026. Promedio de 2 réplicas, en segundos:

| Tamaño | Motor | CSV | Parquet |
|---|---|---|---|
| ×1 | Fila por fila | 0.097 | 0.092 |
| ×1 | Pandera | 0.057 | 0.119* |
| ×20 | Fila por fila | 2.298 | 2.674 |
| ×20 | Pandera | 0.297 | 0.146 |

\* Una de sus dos réplicas tardó 0.188 s y la otra 0.050 s: es ruido de la computadora, no del formato.

**Mal clasificados: 0 de 16 corridas.** Las cuatro configuraciones detectaron todos los inválidos
y no rechazaron ningún registro válido. Ganar velocidad no cuesta calidad.

**ANOVA de efectos fijos** sobre log(segundos) (`anova_2k3.csv`, `efectos_2k3.csv`):

| Término | Efecto (×tiempo) | p | p robusto (HC3) | Lectura |
|---|---|---|---|---|
| B · motor | ×0.26 | 0.0001 | < 0.0001 | Pandera reduce el tiempo a la cuarta parte |
| C · tamaño | ×7.98 | < 0.0001 | < 0.0001 | 20 veces más datos → unas 8 veces más tiempo |
| B × C | ×0.33 | 0.0003 | < 0.0001 | **La ventaja de pandera crece con el tamaño**: en ×1 la diferencia es de milisegundos; en ×20 ahorra más de 2 s |
| A · formato | ×0.97 | 0.87 | 0.91 | Sin efecto detectable con 2 réplicas |
| A × C | ×0.76 | 0.16 | 0.30 | Apunta a que Parquet ayuda en lotes grandes, pero no es significativo aquí |
| A × B, A × B × C | — | ≥ 0.09 | ≥ 0.19 | No significativos |

Gráficas: [`efectos_principales_2k3.png`](../laboratorio/salidas/experimento/efectos_principales_2k3.png),
[`interacciones_2k3.png`](../laboratorio/salidas/experimento/interacciones_2k3.png).

## 4. Supuestos del ANOVA (puerta 3)

| Supuesto | Prueba | Resultado | Decisión |
|---|---|---|---|
| Escala | — | Los tiempos crecen de forma multiplicativa | Se analiza **log(segundos)** |
| Normalidad de residuos | Shapiro-Wilk + Q-Q | p = 0.77 | Se cumple |
| Varianza constante | Breusch-Pagan | p = 0.042 | **No se cumple del todo** |

Como la varianza no es constante, confirmamos los efectos con **errores estándar robustos (HC3)**,
que no dependen de ese supuesto. Las conclusiones no cambian: B, C y B × C siguen con p < 0.0001.
Gráfica: [`supuestos_2k3.png`](../laboratorio/salidas/experimento/supuestos_2k3.png).

*Nota de método:* primero intentamos Levene por tratamiento, pero con 2 réplicas por celda las
desviaciones a la mediana son idénticas dentro de cada grupo y la prueba degenera (dio p ≈ 10⁻¹¹⁸).
Por eso usamos Breusch-Pagan sobre los residuos.

## 5. Combinación óptima y corrida de confirmación

Para el lote grande (C = +1), el modelo predice que la mejor combinación es **Parquet + pandera**:
0.136 s, con un intervalo de predicción al 95 % de 0.049 a 0.377 s. La confirmamos con 5 corridas de
esa combinación y 5 de la configuración actual del pipeline (CSV + pandera), intercaladas en orden
aleatorio (`confirmacion.csv`):

| Configuración | Media (s) | Desv. est. | Mal clasificados |
|---|---|---|---|
| Actual: CSV + pandera | 0.150 | 0.007 | 0 |
| Óptima: Parquet + pandera | **0.094** | 0.003 | 0 |

- La media observada del óptimo (0.094 s) **cae dentro del intervalo de predicción** ✔.
- Mejora observada: **37 % menos tiempo** que la configuración actual (prueba t de Welch sobre log,
  p = 3 × 10⁻⁷). El modelo predecía 50 %; la mejora real es menor, pero clara.
- Con 5 réplicas por lado la confirmación sí detecta el beneficio de Parquet en lotes grandes, algo
  que el 2³, con solo 2 réplicas, no alcanzó a separar del ruido. Es una lección sobre la potencia
  de un diseño.

## 6. Diseño de dos factores con tres niveles

Para ver si el formato importa según el tamaño, medimos solo escritura + lectura de plata con
**formato** (CSV, Parquet, Feather) × **tamaño** (×1, ×10, ×50), 3 réplicas por celda y 27 corridas
en orden aleatorio. Media en segundos:

| Formato | ×1 | ×10 | ×50 |
|---|---|---|---|
| CSV | 0.006 | 0.039 | **0.175** |
| Parquet | 0.008 | 0.013 | 0.028 |
| Feather | 0.006 | 0.010 | 0.024 |

**ANOVA de dos vías con interacción** sobre log(segundos) (`anova_dos_factores.csv`): formato,
tamaño y **la interacción formato × tamaño** son significativos (p < 0.0001). La interacción es la
lectura importante: con los datos reales (×1) los tres formatos tardan lo mismo, unos 6 a 8 ms,
pero con ×50 CSV es 6 a 7 veces más lento que Parquet o Feather. Las líneas de la gráfica
[`interaccion_dos_factores.png`](../laboratorio/salidas/experimento/interaccion_dos_factores.png)
se abren conforme crece el lote.

## 7. Completo 2⁴ contra fraccionado 2⁴⁻¹

Si agregáramos un cuarto factor, **D · motor de lectura de bronce** (pandas `c` vs `pyarrow`):

| | Completo 2⁴ | Fraccionado 2⁴⁻¹ (D = ABC) |
|---|---|---|
| Corridas por réplica | 16 | **8** |
| Con 2 réplicas | 32 | **16 (ahorro de 16 corridas, 50 %)** |
| Matriz | [`matriz_2k4_completo.csv`](../laboratorio/salidas/experimento/matriz_2k4_completo.csv) | [`matriz_2k4-1_fraccionado.csv`](../laboratorio/salidas/experimento/matriz_2k4-1_fraccionado.csv) |
| Relación definidora | — | I = ABCD (resolución IV) |

**Estructura de alias** ([`alias_2k4-1.csv`](../laboratorio/salidas/experimento/alias_2k4-1.csv)):
A = BCD, B = ACD, C = ABD, D = ABC, AB = CD, AC = BD, AD = BC.

**Qué se pierde:** los efectos principales solo se confunden con interacciones de tres factores, que
casi siempre son despreciables, y eso es aceptable. Pero **las interacciones dobles quedan
confundidas en pares**. En nuestro caso eso pesa: la interacción más fuerte que encontramos, B × C
(motor × tamaño), quedaría mezclada con A × D (formato × lector). Con el fraccionado no podríamos
saber cuál de las dos es la real. Por eso, para 4 factores con interacciones dobles importantes,
conviene el completo o una fracción con otro generador.

## 8. Recomendación

1. **Mantener pandera** como motor de la puerta de calidad. El modo fila por fila debe quedar solo
   como respaldo cuando pandera no esté instalado, porque es unas 11 veces más lento en lotes grandes.
2. **Cambiar la capa plata a Parquet cuando los lotes crezcan**, por ejemplo al reprocesar todo el
   histórico o al sumar el DENUE completo: 37 % menos tiempo, confirmado. Con la captura diaria de
   hoy (unos 10 registros) la diferencia es de milisegundos y no justifica el cambio todavía.
3. Esto alimenta la *optimización medida* de E3, con medición antes y después en el pipeline real.

## 9. Transparencia sobre las corridas

El script se corrió tres veces el 26 de noviembre:

1. **Primera corrida:** midió bien (0 mal clasificados), pero el análisis falló por un error de
   código: el factor `C` chocaba con la función `C()` de las fórmulas. Se corrigió el nombre.
2. **Segunda corrida:** completa, con Levene como prueba de varianza. Detectamos que Levene degenera
   con 2 réplicas y la cambiamos por Breusch-Pagan. Sus conclusiones fueron las mismas en B, C y
   B × C; A × C salió significativo ahí (p = 0.02) y aquí no (p = 0.16), así que **no lo tomamos
   como un resultado firme**.
3. **Tercera corrida (la reportada):** medición del 26-nov a las 23:46. Después solo se recalculó el
   análisis con `--solo-analisis` sobre esos mismos datos crudos, para agregar los p-valores HC3.

Los tiempos cambian un poco en cada medición porque dependen de la carga de la computadora. Lo que
se repitió en todas las corridas es lo que reportamos como hallazgo.
