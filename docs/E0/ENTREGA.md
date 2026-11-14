# Entrega E0 · Observatorio veterinario de Colima

Equipo: José Miguel Castellanos · Leonardo Rodríguez García · Etiqueta: `e0` · Tablero: _pendiente_

> Entrega tardía: la fecha era el 6 de noviembre y se entrega el 13 de noviembre.

## Resumen en tres líneas

Observamos la demanda de servicios veterinarios para mascotas con dos fuentes oficiales: el índice
de ingresos de INEGI (224 meses) y el dólar de Banxico (1,729 días). Las dos ya se capturan solas
todos los días con GitHub Actions. La propuesta define la pregunta, el cliente, las tres preguntas
analíticas (pronóstico, experimento 2³ con una veterinaria y perfiles por zona) y el plan de recopilación.

## Rúbrica E0 (una calificación para las tres materias)

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Pregunta y cliente (20) | [Propuesta §1 y §2](propuesta.md) | Pregunta central, quién pagaría y por qué; entrevista con el sector. |
| Preguntas analíticas (20) | [Propuesta §3](propuesta.md) | E1: índice de ingresos a 6 meses. E2: 2³ mensaje × imagen × horario. E3: AGEB de 3 zonas urbanas con ≥ 5 variables. |
| Plan de recopilación (20) | [Propuesta §4](propuesta.md) | 4 fuentes con estructura, formato, frecuencia, acceso, `robots.txt` revisado el 13-nov y términos de uso. |
| Captura y serie histórica (25) | [`captura.yml`](../../.github/workflows/captura.yml), [`data/bronce/`](../../data/bronce/), [`extractores/`](../../extractores/) | Dos fuentes funcionando, una programada diario; serie de 224 meses en bronce. |
| Arranque de calidad (15) | [`calidad/`](../../calidad/), [Propuesta §5](propuesta.md) | Registros individuales de defectos y tiempo, bitácora activa y 3 objetivos con número. |

## Issues de la entrega anterior

No aplica (primera entrega).
