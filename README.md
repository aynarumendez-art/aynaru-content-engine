# Aynaru Content Engine

Tu "Stanley" propio. Cada mañana te propone borradores de LinkedIn y Threads en tu voz,
tú apruebas o editas desde Telegram, y guarda lo aprobado listo para pegar. La publicación
es toque final manual: tú pegas en la app. No toca ninguna API de red social, así que no
se rompe mientras viajas.

## Qué hace
- **Cada lunes** genera el lote completo de la semana: 3 posts (lunes/miércoles/viernes),
  cada uno en versión LinkedIn y Threads, según la rotación de pilares de `rutina.md`.
- Te los manda por Telegram con botones Guardar / Editar / Descartar.
- Editas hablándole normal ("hazlo más corto", "arranca con una pregunta").
- Guarda lo que apruebas en `aprobados/AAAA-MM-DD.md`, listo para agendar o pegar.
- `/lote` genera la semana al instante · `/semana` muestra el plan · `/fuente <link>` saca
  ángulos de un artículo o post (como el modo fuente de Stanley).

## Lo que solo tú puedes hacer (10 minutos, una vez)

**1. Crear el bot de Telegram**
- En Telegram, abre **@BotFather** → `/newbot` → nombre y usuario del bot.
- Te da un **token** (algo como `8123456:AAH...`). Guárdalo.

**2. Conseguir tu chat id**
- Abre **@userinfobot** en Telegram y te dice tu id numérico. Guárdalo.

**3. Tu API key de Claude**
- La de tu cuenta de Anthropic (console.anthropic.com → API Keys).

**4. Configurar**
- Copia `.env.example` como `.env` y pega los tres valores.

## Correr en tu PC (para probarlo hoy)
```bash
cd "C:/Users/Aynaru/aynaru-content-engine"
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python bot.py
```
Escríbele `/start` al bot en Telegram. Luego `/lote` para ver la semana al instante.

## Correr durante el viaje (que no dependa de tu laptop)

El bot necesita estar encendido para mandarte el lote y recibir tus ediciones. Tu laptop
viaja contigo y se apaga, así que se aloja en la nube. **Guía completa en `DESPLIEGUE.md`**
(Railway, todo desde el navegador, sin instalar nada, ~15 min).

## Ajustes rápidos
- Horario del envío diario: `POST_TIME` en `.env`.
- Cuántos borradores por día: `N_BORRADORES`.
- Cambiar cadencia o pilares: edita la tabla en `rutina.md` y el bloque `ROTACION` de `bot.py`.
- Cambiar tu voz o mensajes: edita `marca/contexto-marca.md`.
