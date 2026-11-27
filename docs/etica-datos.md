# Declaración de Ética y Legalidad de Datos

**Observatorio Veterinario de Colima · Trusted Data Lab (TecNM 2026)**  
Entrega E2 · Versión 1.0 · Fecha de emisión: 23 de noviembre de 2026  
Equipo: José Miguel Castellanos (Data Engineer) · Leonardo Rodríguez García (Data Statistician)

---

## 1. Declaración de Principios y Misión Institucional

El Observatorio Veterinario de Colima tiene como misión recolectar, validar, analizar y certificar datos públicos relativos a la oferta, demanda y costos de los servicios veterinarios para mascotas en el Estado de Colima.

Reconocemos que los datos no son neutros: un dato mal capturado, descontextualizado o extraído vulnerando términos normativos induce a errores costosos en las decisiones de negocio y vulnera los derechos fundamentales de los involucrados. Por ello, este observatorio se rige bajo cuatro principios rectores:

1. **Legalidad y Licenciamiento Abierto:** Todo dato capturado proviene de fuentes públicas oficiales con términos de uso explícitos que permiten su reutilización con fines académicos y de investigación.
2. **Cero Datos Personales (Privacidad Absoluta):** Ningún dato que permita identificar a personas físicas es recopilado, procesado ni publicado.
3. **Respeto a la Infraestructura Servidora (Scraping Ético):** Se garantiza una tasa de peticiones controlada, respetando las directivas `robots.txt`, sin provocar sobrecarga ni saturación en servidores públicos.
4. **Transparencia y Trazabilidad:** Todo dato en el observatorio cuenta con linaje auditable desde la capa cruda (Bronce) hasta la analítica (Oro).

---

## 2. Marco Legal Aplicable

### 2.1. Ley del Sistema Nacional de Información Estadística y Geográfica (LSNIEG)
- **Artículos 5, 37 y 38:** La información producida por el Instituto Nacional de Estadística y Geografía (INEGI) es de interés nacional, carácter público y libre consulta. Los usuarios pueden reutilizar y difundir las estadísticas y datos geoespaciales generados por el instituto, con la única obligación de **citar la fuente oficial correspondiente**.

### 2.2. Ley del Banco de México y Normativa de Datos Abiertos
- El Banco de México ofrece el Sistema de Información Económica (SIE) para transparentar indicadores macroeconómicos y financieros del país. El uso de la API del SIE con token de consulta académica y de investigación respeta los límites de volumen establecidos en el portal de desarrolladores.

### 2.3. Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP)
- **Artículos 2, 3 y 8:** La ley tutela los datos personales de personas físicas identificadas o identificables. Los datos de **personas morales** o de **unidades económicas públicas** (nombre comercial, domicilio fiscal o público de un establecimiento, código de actividad económica y coordenadas geográficas) no constituyen datos personales tutelados.
- **Principio de Disociación:** Cualquier información accesoria que pudiera vincularse a una persona física (como el nombre del médico responsable o propietario registrado en padrones mixtos) es disociada o eliminada de manera irreversible en la Capa Bronce antes de su almacenamiento persistente o procesamiento posterior.

### 2.4. Ley Federal del Derecho de Autor (LFDA)
- **Artículo 14:** La ley establece que las ideas, métodos, fórmulas, hechos o datos puros no son susceptibles de protección por derechos de autor. Las series numéricas y catálogos de INEGI y Banxico son datos factuales de libre uso, protegidos en su conjunto mediante las licencias de origen y atribución.

---

## 3. Análisis Detallado por Fuente de Datos

| Dimensión | Fuente 1: INEGI BISE | Fuente 2: Banxico SIE | Fuente 3: INEGI DENUE (E2) | Fuente 4: OpenStreetMap (OSM) |
|---|---|---|---|---|
| **Contenido** | Índice de ingresos de servicios veterinarios para mascotas (SCIAN 541941), base 2018=100. | Tipo de cambio FIX peso mexicano por dólar estadounidense (serie SF43718). | Directorio geoespacial de unidades económicas de mascotas en Colima (SCIAN 541941, 541942, 461121, 812110). | Cartografía vectorial base, nodos viales y puntos de referencia urbanos. |
| **Acceso Técnico** | API REST vía HTTPS con token de desarrollador gratuito. | API REST vía HTTPS con encabezado `Bmx-Token` gratuito. | API REST y descarga de padrón estatal georreferenciado con token gratuito. | Overpass API REST pública (servidores comunitarios). |
| **Análisis de `robots.txt`** | Consultado: `https://www.inegi.org.mx/robots.txt`. Regla activa: `Allow: /app`. La API reside en `/app/api/...`, plenamente **autorizada**. `Disallow` aplica a `/catalog`, `/rnm` y `/metadata`. | Consultado: `https://www.banxico.org.mx/robots.txt`. Redirige a servidor central donde `Disallow` protege `/dyn/`, `/ALEPH/`, `/V/`. El servicio `/SieAPIRest/` **no está restringido**. | Mismo dominio `inegi.org.mx`; `/app/api/denue/...` **autorizada**. Cumple con directiva de peticiones espaciadas. | Consultado: `https://overpass-api.de/api/status`. Política de uso aceptable: máximo 2 hilos simultáneos, no minería masiva sin caché. |
| **Términos de Servicio** | Términos de Libre Uso de la Información del INEGI. Prohíbe alterar la información presentándola como oficial del INEGI si fue manipulada. | Términos de servicio de Banxico SIE API. Prohíbe comercializar los datos como servicio propietario sin atribución. | Términos de Libre Uso del INEGI para el DENUE. Obliga a citar el producto y el periodo de actualización censal. | Open Database License (ODbL) 1.0 de la Fundación OpenStreetMap. Requiere atribución "© Colaboradores de OpenStreetMap". |
| **Licencia de Datos** | Datos abiertos del Gobierno Federal de México (Libre uso con atribución). | Datos abiertos oficiales de Banxico. | Libre uso con atribución (INEGI). | Open Database License (ODbL) / CC BY-SA 2.0. |
| **Licencia del Observatorio** | Se publica bajo **Creative Commons Atribución 4.0 Internacional (CC BY 4.0)**, permitiendo su libre uso con cita al equipo TDL. | Se publica bajo **CC BY 4.0**. | Se publica bajo **CC BY 4.0**. | Compatible con **ODbL** en capas de combinación cartográfica. |

---

## 4. Protocolo de Extracción Ética (Scraping y Consumo de APIs)

Todas las extracciones automatizadas del proyecto pasan obligatoriamente por el módulo `extractores/base.py` (`ExtractorEtico`), el cual implementa de manera estricta los siguientes mecanismos técnicos:

1. **Identificación Transparente (User-Agent Institucional):**  
   Toda petición HTTP viaja con el encabezado:  
   `User-Agent: TDL-Observatorio/1.0 (proyecto academico; contacto: <TDL_CONTACTO>)`  
   Esto permite a los administradores de los servidores contactar de inmediato al equipo ante cualquier inquietud o anomalía técnica.

2. **Control de Frecuencia y Rate Limiting (Crawl-Delay):**  
   - Se establece una pausa obligatoria mínima de **1.5 segundos** entre peticiones sucesivas al mismo dominio.
   - Si el `robots.txt` especifica un valor de `Crawl-delay` superior, el extractor adopta automáticamente dicho valor (`max(1.5, crawl_delay)`).

3. **Manejo de Saturación y Retroceso Exponencial (Exponential Backoff):**  
   - Si el servidor responde con un código HTTP `429 Too Many Requests` o `5xx Server Error`, el extractor no reintenta inmediatamente. Aplica una espera exponencial: `espera = pausa * 2^i` (donde $i$ es el número de intento).
   - Se limita a un máximo de 3 intentos; tras agotar los reintentos, aborta con excepción controlada registrando la falla en `calidad/bitacora_capturas.csv`.

4. **No Evasión de Controles:**  
   El observatorio no utiliza técnicas de evasión de proxys dinámicos, spoofing de encabezados ni resolución de CAPTCHAs. Si un endpoint o sitio requiere autenticación no disponible o prohíbe el acceso mediante `robots.txt`, la fuente es rechazada y se busca una alternativa abierta.

---

## 5. Privacidad y Política Estricta de "Cero Datos Personales"

En estricto cumplimiento con la **Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP)**, el observatorio implementa una política de segregación y sanitización en Capa Bronce:

### 5.1. Distinción de Datos
- **Datos que se conservan:** identificador del DENUE y CLEE, nombre comercial del establecimiento, clave y descripción de la actividad (SCIAN), estrato de personal ocupado (por ejemplo, "0 a 5 personas"), tipo de vialidad, calle, número exterior, colonia, código postal, AGEB, manzana, fecha de alta, municipio y coordenadas.
- **Datos que nunca se guardan:** la **razón social** (en una persona física es su nombre completo), el **teléfono**, el **correo electrónico** y el **sitio web**. La API del DENUE sí los devuelve, pero el extractor no los copia.

### 5.2. Mecanismo de Sanitización Técnica
El extractor `extractores/denue.py` trabaja con una **lista blanca** (`CAMPOS`): de cada establecimiento que devuelve la API solo copia los campos de la lista de arriba. Lo que no está en la lista no llega nunca a `data/bronce/denue/`. Además, `sanitizar_privacidad(df)` elimina cualquier columna de la lista `CAMPOS_PERSONALES` que aparezca por error. Esto lo verifica la prueba `test_capturar_no_guarda_datos_personales_ni_el_token`, con una respuesta simulada que trae razón social, teléfono y correo.

### 5.3. Decisión sobre el nombre comercial
Algunos negocios pequeños usan el nombre de su dueña o dueño como nombre comercial (por ejemplo, "Estética Canina" seguida de un nombre propio). Decidimos **conservar el nombre comercial** porque es el nombre público con el que el establecimiento se anuncia y con el que INEGI lo publica en el DENUE; no es un dato de contacto ni identifica a la persona fuera de su negocio. Si un establecimiento pidiera no aparecer, se elimina su registro. Mostrar solo el giro, sin nombre, queda como alternativa si el equipo docente lo considera necesario.

### 5.4. Corrección del 27 de noviembre de 2026
Hasta esa fecha, el extractor del DENUE usaba, sin avisar, una lista de 45 establecimientos escritos a mano cuando la API fallaba, y esa lista llegó a bronce marcada como `inegi-denue`. Esos registros se eliminaron de todas las capas. Desde entonces la captura usa solo la API oficial (con `DENUE_TOKEN`), y si falla lo registra en la bitácora sin sustituir los datos.

---

## 6. Diagnóstico y Mitigación de Sesgos Estadísticos y de Información

Todo conjunto de datos refleja sesgos derivados de su metodología de captura. El observatorio identifica y mitiga los siguientes cuatro sesgos críticos:

### 6.1. Sesgo de Cobertura Formal (DENUE)
- **Diagnóstico:** El DENUE de INEGI recopila unidades económicas identificadas formalmente durante los Censos Económicos y actualizaciones de campo. Omite la actividad veterinaria informal, servicios de paseo canino o consultas a domicilio no registradas ante el SAT o el municipio.
- **Impacto:** Puede subestimar la oferta real de servicios en zonas de menores ingresos o periferias urbanas.
- **Mitigación:** En el tablero público y en los reportes ejecutivos se declara de manera explícita que las métricas corresponden a la **oferta formalmente registrada**. Se complementa el análisis con estratos de tamaño de personal para distinguir entre consultorios individuales y hospitales consolidados.

### 6.2. Sesgo de Rezago Temporal (Lag en Encuesta Mensual de Servicios - INEGI)
- **Diagnóstico:** La EMS de INEGI presenta un rezago habitual de 60 a 75 días entre el periodo reportado y la fecha de publicación oficial (por ejemplo, en noviembre se publica el dato correspondiente a septiembre).
- **Impacto:** Un cliente que toma decisiones hoy podría guiarse por una situación económica de hace dos meses.
- **Mitigación:** El Laboratorio Estadístico incorpora pronósticos estocásticos (SES, Holt-Winters, ARIMA) con intervalos de predicción al 95 % para proyectar el periodo rezagado y los meses subsiguientes, advirtiendo al usuario sobre el margen de error muestral del modelo.

### 6.3. Sesgo de Granularidad y Frecuencia Temporal (Banxico vs. INEGI)
- **Diagnóstico:** Banxico publica el tipo de cambio diariamente (días hábiles), mientras que INEGI reporta los ingresos mensualmente.
- **Impacto:** Un análisis directo entre ambas series crudas provocaría desalineación temporal o distorsión por volatilidad de corto plazo (ruido diario).
- **Mitigación:** En la Capa Plata se conserva la granularidad original diaria para auditoría, y en la Capa Oro se realiza una agregación mensual controlada (`usd_mxn_mensual.csv`) calculando la media mensual y el valor de cierre, contabilizando el número exacto de días hábiles observados (`n_obs`) y excluyendo el mes en curso por estar incompleto.

### 6.4. Sesgo de Concentración Geográfica (Urbano vs. Rural)
- **Diagnóstico:** Los establecimientos especializados en mascotas tienden a agruparse en la Zona Metropolitana de Colima–Villa de Álvarez y en el puerto de Manzanillo, existiendo escasa cobertura en municipios como Minatitlán, Ixtlahuacán o Coquimatlán.
- **Impacto:** Comparar municipios por totales absolutos distorsiona la capacidad real de atención a la población animal.
- **Mitigación:** En la Capa Oro (`denue_resumen_municipal.csv`), los establecimientos se clasifican por zonas funcionales (`zona_urbana`) y se separan por categoría de actividad (veterinarias de pequeñas especies vs forrajeras pecuarias vs estéticas), facilitando un análisis de perfiles multivariados en E3.

---

## 7. Matriz de Control de Riesgos Éticos y Legales

| Riesgo Identificado | Probabilidad | Impacto | Control Implementado | Estado |
|---|---|---|---|---|
| Exposición involuntaria de API tokens en GitHub | Media | Crítico | Variables de entorno (`INEGI_TOKEN`, `BANXICO_TOKEN`), secret masking en CI y escaneo preventivo con `gitleaks`. | Controlado (0 secretos en historial) |
| Bloqueo o baneo de IP por exceso de peticiones | Baja | Alto | Pausa de 1.5 s entre peticiones, lectura de `robots.txt` y User-Agent identificable en `extractores/base.py`. | Controlado |
| Captura involuntaria de datos personales en DENUE | Baja | Crítico | Función `sanitizar_privacidad` en Capa Bronce que descarta campos de personas físicas antes de guardar. | Verificado con prueba unitaria |
| Corrupción de datos por falta de trazabilidad | Media | Alto | Metadatos mandatorios en Capa Oro: `archivo_bronce_origen`, `fecha_ingesta` y `fuente_origen`. | Verificado con prueba unitaria |
| Interpretación errónea de pronósticos por el cliente | Alta | Medio | Intervalo de predicción al 95 %, prueba de Ljung-Box y texto explicativo en lenguaje claro en el tablero. | Controlado |

---

## 8. Licencia de Publicación del Observatorio

El Observatorio Veterinario de Colima, su código fuente, documentación y conjuntos de datos derivados en Capa Oro se liberan bajo los términos de la licencia internacional **Creative Commons Atribución 4.0 Internacional (CC BY 4.0)**.

Usted es libre de:
- **Compartir:** copiar y redistribuir el material en cualquier medio o formato.
- **Adaptar:** remezclar, transformar y construir a partir del material para cualquier propósito, incluso comercial.

Bajo los siguientes términos:
- **Atribución:** Debe dar crédito de manera adecuada a los autores (José Miguel Castellanos y Leonardo Rodríguez García / Trusted Data Lab TecNM), brindar un enlace a la licencia e indicar si se han realizado cambios.
