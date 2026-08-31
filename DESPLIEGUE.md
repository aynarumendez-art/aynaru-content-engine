# Desplegar en Railway (24/7, sin instalar nada en tu equipo)

Objetivo: que el bot corra en la nube y te mande el lote cada lunes, aunque tu laptop esté
apagada de viaje. Todo esto se hace desde el navegador. Tiempo estimado: 15-20 minutos.

## Antes de empezar, ten a la mano
- **Token de Telegram**: en Telegram abre @BotFather → `/newbot` → sigue los pasos → copia el token.
- **Tu chat id**: abre @userinfobot en Telegram → copia tu número.
- **API key de Claude**: console.anthropic.com → API Keys → crea una.

## Paso 1 · Subir el código a GitHub (privado)
1. Crea cuenta en github.com si no tienes.
2. Botón **New repository** → nombre `aynaru-content-engine` → marca **Private** → Create.
3. En el repo vacío: **Add file → Upload files**. Arrastra TODO el contenido de la carpeta
   `C:\Users\Aynaru\aynaru-content-engine` EXCEPTO el archivo `.env` (ese nunca se sube).
   Sí sube: `bot.py`, `requirements.txt`, `Procfile`, `.gitignore`, `marca/`, `rutina.md`, etc.
4. **Commit changes**.

## Paso 2 · Conectar Railway
1. Crea cuenta en railway.app (entra con GitHub, es lo más rápido).
2. **New Project → Deploy from GitHub repo** → elige `aynaru-content-engine`.
3. Railway detecta Python solo (por `requirements.txt`) y usa el `Procfile` (proceso `worker`).

## Paso 3 · Poner las variables secretas
En el proyecto de Railway → pestaña **Variables** → agrega estas (una por una):

| Variable | Valor |
|---|---|
| `TELEGRAM_TOKEN` | el token de BotFather |
| `TELEGRAM_CHAT_ID` | tu chat id |
| `ANTHROPIC_API_KEY` | tu API key de Claude |
| `TZ` | `America/Mexico_City` |
| `POST_TIME` | `07:30` (opcional) |

Guarda. Railway redespliega solo.

## Paso 4 · Probar
1. En Telegram, abre tu bot y manda `/start`. Debe responder con el plan de la semana.
2. Manda `/lote`. En un minuto te llegan los 3 posts de la semana.
3. A partir de ahí, cada lunes 07:30 (CDMX) llega solo.

## Notas
- El plan gratuito de Railway suele bastar para un bot así. Si te pide upgrade, es del orden
  de 5 USD/mes.
- Si prefieres Render.com o Replit, el patrón es el mismo: subes el repo, pones las variables,
  y corre como worker. Pídeme el paso a paso de ese si lo eliges.
- Los posts guardados con el botón viven en el servidor y pueden borrarse en un redepliegue,
  pero no importa: siempre los tienes en el chat de Telegram para copiar.
