# Propuesta E0 · Observatorio veterinario de Colima

Equipo: José Miguel Castellanos · Leonardo Rodríguez García
Repositorio: https://github.com/Miguel-iso21/Trusted_Data_Lab

---

## 1. Ficha del observatorio

| | |
|---|---|
| **Sector** | Servicios veterinarios para mascotas (SCIAN 541941) y su cadena de insumos |
| **Región** | Estado de Colima; tendencias nacionales como referencia, porque INEGI no publica el indicador mensual por estado |
| **Pregunta central** | ¿Qué va a pasar con la demanda de servicios veterinarios en los próximos meses, qué la mueve y en qué zonas de Colima hay más o menos oferta para mascotas? |
| **Quién pagaría por la respuesta** | Veterinarias independientes de Colima, que deciden inventario, horarios, precios y publicidad sin datos. También distribuidoras de medicamentos y alimento para mascotas, que deciden a qué zonas ampliar su ruta, y el colegio de médicos veterinarios del estado, para informar a sus agremiados. |
| **Por qué pagarían** | Una veterinaria pequeña no tiene quién lea INEGI ni Banxico por ella. El observatorio le dice si viene una temporada alta o baja, si el dólar va a encarecer sus insumos importados y qué tipo de publicación le trae más clientes, con evidencia y no con rumores. |

## 2. Entrevista con el sector

| | |
|---|---|
| **Entrevistado** | Médico veterinario, dueño de una clínica veterinaria en Colima (no publicamos su nombre) |
| **Fecha y duración** | 9 de noviembre de 2026 · 20 minutos |
| **Medio** | Llamada telefónica |

| # | Pregunta | Respuesta |
|---|---|---|
| 1 | ¿Llevan registros de consultas o ventas por mes de los últimos 3 años, aunque sea en cuaderno? | Sí. |
| 2 | ¿Qué es lo que más le preocupa: perder clientes, quedarse sin inventario o que le suban los costos? | Quedarse sin inventario. |
| 3 | ¿En qué meses del año tiene más trabajo y en cuáles menos? ¿Por qué cree que pasa? | El trabajo es constante todo el año. Solo baja en septiembre, por la entrada a clases, y en noviembre, por la Feria de Colima. |
| 4 | Cuando sube el dólar, ¿le suben los precios sus proveedores? | Todo sube a principio de año, al menos una vez. No nota mucha variación cuando sube el dólar. |
| 5 | ¿Cada cuánto hace pedidos a sus proveedores, cómo decide cuánto comprar y qué productos se le acaban más seguido? | Hace pedidos una vez a la semana de vacunas, alimento y medicamentos varios; solo rellena su stock. En verano y en temporada de lluvias compra más productos contra pulgas y garrapatas (jabones, shampoos y pastillas). Lo que se le acaba más rápido son las vacunas. |

> Las preguntas 3 a 5 se hicieron en una llamada de seguimiento con el mismo veterinario
> (24 de noviembre de 2026, por teléfono), porque perdimos las notas originales de esas preguntas.

**Lo que aprendimos:**

- **La estacionalidad que importa es local.** El veterinario identifica dos meses flojos, septiembre
  (entrada a clases) y noviembre (Feria de Colima), que el índice nacional de INEGI no puede mostrar.
  Lo comparamos con la descomposición estacional de E1, y sus registros mensuales de 3 años serían
  la serie ideal para confirmarlo en Colima.
- **El dólar no se traslada a precios de inmediato.** Sus proveedores ajustan precios una vez al año,
  en enero. Eso cambia nuestra hipótesis: más que una correlación mes a mes, esperamos un efecto
  rezagado y concentrado a inicio de año. La correlación cruzada lo tiene que comprobar, no suponer.
- **El inventario se decide cada semana y por producto.** El pronóstico mensual le sirve para
  planear, pero lo que le cuesta dinero es quedarse sin **vacunas** y no anticipar la temporada de
  pulgas y garrapatas (verano y lluvias). Por eso el observatorio debe hablar de temporadas y de
  productos concretos, no solo de un índice general.

## 3. Tres preguntas analíticas

### E1 · Pronóstico (series de tiempo)
**¿Cuál será el índice de ingresos de los servicios veterinarios para mascotas en los próximos
6 meses, con su intervalo de confianza al 95 %?**

- Variable: índice de ingresos totales, SCIAN 541941, base 2018 = 100 (INEGI BISE, indicador 716898), mensual.
- Historia: 224 meses (enero 2008 a agosto 2026), muy por encima del mínimo de 36.
- Cómo se mide el éxito: el modelo se elige por su error (MAE, RMSE y MAPE) en los últimos 12
  meses, que no ve al entrenarse.
- Segunda variable para la correlación cruzada: tipo de cambio FIX promedio mensual (Banxico SF43718).
  Hipótesis: un dólar más caro encarece los insumos importados y se refleja en los ingresos con
  algunos meses de rezago.

### E2 · Experimento factorial (ruta ingeniería)
**¿Qué configuración de la puerta de calidad (bronce → plata) procesa los datos en menos tiempo
sin dejar de detectar los registros inválidos?**

| Factor | Nivel − | Nivel + |
|---|---|---|
| A · Formato de escritura de la capa plata | CSV | Parquet |
| B · Motor de validación | Fila por fila (pandas `iterrows`) | Vectorizado (pandera) |
| C · Tamaño del lote | Datos reales de Banxico (×1) | Datos replicados ×20 |

- Diseño 2³ = 8 tratamientos × 2 réplicas = 16 corridas en orden aleatorio, con semilla guardada.
- Respuestas: tiempo de procesamiento en segundos y registros mal clasificados. Se inyecta un 2 %
  de registros inválidos conocidos, y la puerta debe mandarlos todos a cuarentena.
- Bloqueo: cada réplica se corre como un bloque, porque el estado de la computadora (caché, otros
  programas) cambia entre tandas.
- Se corre contra una copia local de los datos de bronce, nunca contra las APIs de INEGI o Banxico.
- Además: un diseño de dos factores con tres niveles (formato CSV/Parquet/Feather × tamaño
  ×1/×10/×50), la comparación de un 2⁴ completo contra un 2⁴⁻¹ fraccionado y una corrida de
  confirmación de la mejor combinación.

> **Cambio de ruta.** En la primera versión de esta propuesta el experimento era de negocio: un 2³
> de mensaje × imagen × horario en las publicaciones de la veterinaria entrevistada. No conseguimos
> confirmar el acuerdo a tiempo para correr 16 publicaciones, así que el 26 de noviembre pasamos a la
> ruta de ingeniería, que el proyecto también contempla. La ruta de negocio queda como trabajo futuro
> con el mismo veterinario.

### E3 · Comparación multivariada (PCA y MANOVA)
**¿Las tres zonas urbanas de Colima (Colima–Villa de Álvarez, Manzanillo y Tecomán) tienen perfiles
distintos de oferta de servicios para mascotas?**

- Unidad de análisis: área geoestadística básica (AGEB) urbana.
- Grupos: las 3 zonas urbanas.
- Variables por AGEB (≥ 5): veterinarias, tiendas de mascotas y estéticas caninas por cada 10,000
  habitantes (DENUE de INEGI); proporción de establecimientos de 0 a 5 empleados; distancia
  promedio a la veterinaria más cercana; población y viviendas habitadas (Censo 2020 de INEGI).
- Resultado para el cliente: un mapa de zonas parecidas que muestra dónde hay muchas mascotas y
  poca oferta.

## 4. Plan de recopilación

| | Fuente 1 · INEGI BISE | Fuente 2 · Banxico SIE | Fuente 3 (E2/E3) · INEGI DENUE | Fuente 4 (E3) · Censo 2020 por AGEB |
|---|---|---|---|---|
| **Qué** | Índice de ingresos de servicios veterinarios para mascotas (716898) | Tipo de cambio FIX MXN/USD (SF43718) | Negocios con giro, tamaño y coordenadas | Población y viviendas por AGEB |
| **Estructura** | JSON: `Series[].OBSERVATIONS[]` con `TIME_PERIOD` y `OBS_VALUE` | JSON: `bmx.series[].datos[]` con `fecha` (dd/mm/aaaa) y `dato` (texto, `N/E` si no hay) | JSON, un registro por establecimiento | CSV por entidad |
| **Frecuencia de la fuente** | Mensual, con unos 2 meses de rezago | Diaria, solo días hábiles | Actualización periódica del directorio | Censal (2020) |
| **Nuestra captura** | Diaria a las 08:00 (GitHub Actions), para detectar la publicación nueva | Diaria a las 08:00: últimos 15 días | Una vez por entrega | Una sola vez |
| **Método de acceso** | API REST con token gratuito | API REST con token gratuito (encabezado `Bmx-Token`) | API REST con token gratuito | Descarga de archivo |
| **robots.txt** | Revisado el 13-nov-2026: `Allow: /app`; la API vive en `/app/api/...`, **permitida**. Los `Disallow` solo afectan `/catalog`, `/rnm` y `/metadata` | Revisado el 13-nov-2026: `www.banxico.org.mx/robots.txt` redirige a `anterior.banxico.org.mx/robots.txt`, que bloquea `/dyn`, `/ALEPH` y `/V`; `/SieAPIRest/` **no está bloqueado** | Mismo `robots.txt` de INEGI: **permitida** | Descarga directa, sin scraping |
| **Términos de uso** | Términos de Libre Uso de la Información del INEGI: se permite reutilizar citando la fuente. El token es personal y no se publica | Uso del SIE API con token personal y límites de consultas; los revisaremos en su documentación vigente. El token no se publica | Libre uso de INEGI, citando la fuente; los datos son de establecimientos, no de personas | Libre uso de INEGI |
| **Datos personales** | No hay, es un índice agregado | No hay, es un tipo de cambio | El DENUE puede traer nombre del propietario y teléfono: se eliminan en bronce antes de guardar | No hay, son agregados por AGEB |

**Cómo cumplimos con las reglas de scraping ético:** todas las peticiones pasan por
`extractores/base.py`. Ese módulo lee `robots.txt` y su `Crawl-delay` antes de pedir algo, se
identifica con el User-Agent `TDL-Observatorio/1.0 (proyecto academico; contacto: …)`, espera al
menos 1.5 s entre peticiones al mismo dominio y reintenta con espera exponencial ante un 429 o un 5xx.

## 5. Estado de la captura y del sistema de calidad

| Componente | Estado al 13-nov-2026 | Evidencia |
|---|---|---|
| Dos fuentes funcionando | INEGI y Banxico capturando | `data/bronce/inegi/`, `data/bronce/banxico/` |
| Captura programada | GitHub Actions todos los días a las 08:00 (Colima). La primera ejecución en Actions (lanzada a mano el 13-nov a las 19:00) terminó bien; la programada corre sola desde el 14-nov | `.github/workflows/captura.yml`, commit `c1cb078` |
| Metadatos de captura en bronce | `fuente`, `url_origen` (sin token) y `capturado_en` (UTC) en cada registro | `data/bronce/` |
| Serie histórica | 224 meses de ingresos veterinarios y 1,729 días de dólar | `data/bronce/` |
| Registro de defectos individual | Uno por integrante | `calidad/defectos-*.csv` |
| Registro de tiempo individual | Uno por integrante | `calidad/tiempo-*.csv` |
| Bitácora de ejecuciones | Activa: cada captura escribe hora, fuente, estado, filas, segundos y error | `calidad/bitacora_capturas.csv` |

**Tres objetivos de calidad medibles** (se detallan en `docs/plan-sqa.md`):

1. **Disponibilidad de la captura ≥ 95 %**, medida con la bitácora en ventanas de 14 días.
2. **Tasa de rechazo de la puerta de calidad ≤ 5 %** por fuente. Si se supera, el pipeline se detiene.
3. **Cobertura de pruebas automáticas ≥ 60 %**, verificada en cada push por la integración continua.

## 6. Nota sobre la fecha de entrega

Esta propuesta se etiqueta como `e0` el 26 de noviembre, después de la fecha de E0 (6 de
noviembre). Casi toda se escribió el 13 de noviembre; la entrevista se completó con la llamada de
seguimiento del 24 de noviembre y el experimento pasó a la ruta de ingeniería el 26. La captura
automática empezó el 13 de noviembre, así que la medición de fiabilidad de 7 días no estuvo lista
para E1. Lo registramos como lección del proyecto: la captura tenía que arrancar primero, porque
todo lo demás depende de su historia.
