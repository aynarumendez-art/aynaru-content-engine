# Rutina y estrategia de publicación — Aynaru

> La constancia no depende de fuerza de voluntad. Depende de decisiones ya tomadas.
> Este archivo es la fuente de la cadencia. El bot lo respeta.

## Cadencia (modo viaje, sostenible en 20 días)
- **LinkedIn: 3 posts/semana** (lunes, miércoles, viernes). Canal prioritario.
- **Threads: 1 al día opcional**, versión corta y punzante del mismo ángulo del día.
- Sin blog ni newsletter durante el viaje.

## Mezcla
- 70% autoridad / 30% atracción de clientes.
- Máximo 2 piezas del mismo pilar por semana. Rotar los 5 pilares.

## Calendario rotativo de pilares (3 semanas, se repite)
El bot calcula el pilar del día con esta tabla (día de la semana + número de semana):

| Semana | Lunes            | Miércoles      | Viernes                 |
|--------|------------------|----------------|-------------------------|
| 1      | VALOR ECONÓMICO  | ESCALA         | DOCUMENTACIÓN           |
| 2      | DECISIONES       | COHERENCIA     | Opinión / social proof  |
| 3      | VALOR ECONÓMICO  | ESCALA         | DECISIONES              |

Los días sin post de LinkedIn (martes, jueves, fin de semana) el bot puede proponer solo
un Threads corto si lo pides con /hoy, pero no envía nada automático.

## Entrega semanal (modo viaje · tu parte: ~10 minutos, una vez por semana)
1. **Cada lunes en la mañana** el bot genera el lote completo de la semana: los 3 posts
   (lunes, miércoles, viernes) con su pilar ya asignado, cada uno en versión LinkedIn
   (150-300 palabras) y Threads (corta, < 500 caracteres).
2. Te llegan por Telegram con botones: Guardar / Editar / Descartar.
3. Editas lo que quieras hablándole normal ("más corto", "otro gancho").
4. Lo que guardas queda en `aprobados/AAAA-MM-DD.md`, con formato listo para pegar.
5. Agendas los 3 de una (en LinkedIn nativo o donde programes) y te olvidas hasta el
   siguiente lunes. Ese es el único paso manual.

## Horario de envío
- Lote semanal: lunes 07:30 (hora CDMX). Configurable en `.env` (POST_TIME, TZ).
- Horario sugerido para publicar cada pieza: 08:00-09:00 o 12:00-13:00 entre semana.

## Comandos del bot
- `/lote` — genera el lote de la semana ahora mismo (sin esperar al lunes).
- `/semana` — te muestra el plan de pilares de la semana en curso.
- `/aprobados` — te muestra lo que ya guardaste, listo para pegar.
- `/fuente <link>` — le pasas un artículo o post y saca ángulos para ti (modo Stanley).
