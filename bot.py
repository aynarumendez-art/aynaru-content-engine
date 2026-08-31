"""
Aynaru Content Engine — bot de Telegram (modo lote semanal).

Cada lunes en la mañana genera el paquete completo de la semana (3 posts de LinkedIn +
sus versiones de Threads), en la voz de Aynaru, y te lo manda a Telegram listo para agendar.
Publicación: toque final manual (tú pegas/agendas en la app). No toca ninguna API de red social.
"""

import os
import re
import json
import uuid
import asyncio
import logging
import datetime as dt
from pathlib import Path

import anthropic
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, Defaults, filters,
)

# ---------------------------------------------------------------- configuración
BASE = Path(__file__).parent
CONTEXTO_MARCA = (BASE / "marca" / "contexto-marca.md").read_text(encoding="utf-8")
_voz = BASE / "marca" / "voz-ejemplos.md"
if _voz.exists():
    CONTEXTO_MARCA += "\n\n" + _voz.read_text(encoding="utf-8")
APROBADOS = BASE / "aprobados"
APROBADOS.mkdir(exist_ok=True)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])          # solo tú puedes usar el bot
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]    # el SDK la toma del entorno
MODEL = os.environ.get("MODEL", "claude-sonnet-5")
POST_TIME = os.environ.get("POST_TIME", "07:30")       # HH:MM en la zona de abajo
TZ = os.environ.get("TZ", "America/Mexico_City")
USE_WEB_SEARCH = os.environ.get("USE_WEB_SEARCH", "1") == "1"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("aynaru-bot")
_ws_id = os.environ.get("ANTHROPIC_WORKSPACE_ID", "").strip()
_anthropic_kw = {}
if _ws_id:
    _anthropic_kw["default_headers"] = {"anthropic-workspace-id": _ws_id}
cliente = anthropic.Anthropic(**_anthropic_kw)

# ------------------------------------------------------------- rotación pilares
# Semana (índice 0-2) -> día de publicación -> pilar. La semana rota cada 3.
ROTACION = {
    0: {"lunes": "VALOR ECONÓMICO", "miércoles": "ESCALA", "viernes": "DOCUMENTACIÓN"},
    1: {"lunes": "DECISIONES", "miércoles": "COHERENCIA", "viernes": "Opinión / social proof"},
    2: {"lunes": "VALOR ECONÓMICO", "miércoles": "ESCALA", "viernes": "DECISIONES"},
}


def slots_semana(fecha: dt.date):
    """Los 3 posts de la semana: [(día, pilar), ...]."""
    wk = (fecha.isocalendar().week - 1) % 3
    r = ROTACION[wk]
    return [("lunes", r["lunes"]), ("miércoles", r["miércoles"]), ("viernes", r["viernes"])]


# --------------------------------------------------------------- generación IA
def _texto(resp) -> str:
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _extraer_json(texto: str):
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", texto, re.DOTALL)
    crudo = m.group(1) if m else texto[texto.find("["): texto.rfind("]") + 1]
    return json.loads(crudo)


def _llamar(system: str, prompt: str, con_busqueda: bool, max_tokens: int = 4000):
    kwargs = dict(model=MODEL, max_tokens=max_tokens, system=system,
                  messages=[{"role": "user", "content": prompt}])
    if con_busqueda:
        kwargs["tools"] = [{"type": "web_search_20260209",
                            "name": "web_search", "max_uses": 3}]
    return cliente.messages.create(**kwargs)


def generar_lote_semanal():
    """Genera el paquete completo de la semana en una sola llamada."""
    fecha = dt.date.today()
    slots = slots_semana(fecha)
    lista = "\n".join(f"- {dia.capitalize()}: pilar {pilar}" for dia, pilar in slots)
    prompt = f"""Hoy es {fecha.isoformat()}, inicio de semana. Prepara el LOTE COMPLETO de la
semana para Aynaru: un post por cada día de publicación, con su pilar ya asignado:
{lista}

Primero investiga en la web QUÉ le preocupa y de qué habla hoy un dueño de pyme o fundador
en México y Latinoamérica (ventas, costos, contratar, delegar, crecer, competencia). Busca
en su lenguaje, no en el del diseño. Usa uno o dos de esos temas reales para anclar al menos
un post, de modo que le hable directo a lo que al dueño ya le interesa. Nunca inventes cifras
ni casos: si no hay fuente, escribe desde la experiencia de Aynaru, sin datos específicos.

Para cada día escribe un post de LinkedIn (150-300 palabras) y una versión de Threads
(corta, menos de 500 caracteres, punzante). Los tres posts deben ser DISTINTOS entre sí:
no repitas gancho ni estructura. Respeta TODAS las reglas de voz (incluida: nunca uses la
raya larga como pausa).

Responde SOLO con un array JSON en un bloque ```json, sin texto antes ni después.
Cada elemento: {{"dia": "lunes|miércoles|viernes", "pilar": "...", "gancho": "...",
"angulo": "de qué trata en 1 línea", "linkedin": "post completo", "threads": "versión corta"}}"""
    try:
        resp = _llamar(CONTEXTO_MARCA, prompt, USE_WEB_SEARCH, max_tokens=8000)
        return _extraer_json(_texto(resp))
    except Exception as e:                       # p. ej. sin acceso a web_search
        log.warning("Reintento sin búsqueda web: %s", e)
        resp = _llamar(CONTEXTO_MARCA, prompt, False, max_tokens=8000)
        return _extraer_json(_texto(resp))


def regenerar_uno(borrador: dict, instrucciones: str):
    prompt = f"""Este es un borrador tuyo ({borrador.get('dia','')}, pilar {borrador.get('pilar')}):

LinkedIn:
{borrador.get('linkedin','')}

Threads:
{borrador.get('threads','')}

Aynaru pide este cambio: "{instrucciones}"

Reescríbelo respetando su voz y todas las reglas. Responde SOLO con un array JSON de un
solo elemento, mismo formato: {{"dia","pilar","gancho","angulo","linkedin","threads"}}."""
    resp = _llamar(CONTEXTO_MARCA, prompt, False, max_tokens=1500)
    return _extraer_json(_texto(resp))[0]


# ------------------------------------------------------------------ helpers TG
def solo_duena(func):
    async def wrap(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat and update.effective_chat.id != CHAT_ID:
            return
        return await func(update, context)
    return wrap


def _tarjeta(b: dict) -> str:
    partes = [f"{b.get('dia','').upper()} · {b.get('pilar','')}",
              b.get('angulo', ''), ""]
    if b.get("linkedin"):
        partes += ["LinkedIn:", b["linkedin"], ""]
    if b.get("threads"):
        partes += ["Threads:", b["threads"]]
    return "\n".join(partes)


def _botones(bid: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Guardar", callback_data=f"ap:{bid}"),
        InlineKeyboardButton("✏️ Editar", callback_data=f"ed:{bid}"),
        InlineKeyboardButton("🗑️ Descartar", callback_data=f"ds:{bid}"),
    ]])


async def _enviar_lote(bot, chat_id, borradores, store):
    for b in borradores:
        bid = uuid.uuid4().hex[:8]
        store[bid] = b
        await bot.send_message(chat_id, _tarjeta(b), reply_markup=_botones(bid))


# --------------------------------------------------------------- comandos bot
@solo_duena
async def cmd_start(update, context):
    slots = slots_semana(dt.date.today())
    plan = "\n".join(f"· {d.capitalize()}: {p}" for d, p in slots)
    await update.message.reply_text(
        "Motor de contenido de Aynaru, listo.\n\n"
        f"Plan de esta semana:\n{plan}\n\n"
        "Comandos: /lote (genera la semana ahora)  /semana (ver plan)  "
        "/aprobados  /fuente <link>", parse_mode=ParseMode.MARKDOWN)


@solo_duena
async def cmd_semana(update, context):
    slots = slots_semana(dt.date.today())
    plan = "\n".join(f"· {d.capitalize()}: {p}" for d, p in slots)
    await update.message.reply_text(f"Plan de esta semana:\n{plan}")


@solo_duena
async def cmd_lote(update, context):
    await update.message.reply_text("Generando el lote de la semana...")
    try:
        borradores = await asyncio.to_thread(generar_lote_semanal)
    except Exception as e:
        log.exception("Error generando lote")
        await update.message.reply_text(f"⚠️ No pude generar el lote: {type(e).__name__}: {e}")
        return
    if not borradores:
        await update.message.reply_text("No obtuve borradores. Intenta otra vez con /lote.")
        return
    context.application.bot_data.setdefault("drafts", {})
    await _enviar_lote(context.bot, CHAT_ID, borradores,
                       context.application.bot_data["drafts"])


@solo_duena
async def cmd_aprobados(update, context):
    hoy = APROBADOS / f"{dt.date.today().isoformat()}.md"
    if hoy.exists():
        await update.message.reply_text(hoy.read_text(encoding="utf-8")[:3500])
    else:
        await update.message.reply_text("Aún no has guardado nada hoy.")


@solo_duena
async def cmd_fuente(update, context):
    if not context.args:
        await update.message.reply_text("Uso: /fuente <link>")
        return
    url = context.args[0]
    await update.message.reply_text("Analizando la fuente...")
    prompt = (f"Analiza esta fuente: {url}\nExtrae hasta 3 ángulos que conecten con los 5 "
              "pilares de Aynaru y su posicionamiento. Por cada uno: IDEA, PILAR, ÁNGULO "
              "PARA AYNARU, FORMATO SUGERIDO. Texto claro, no JSON.")
    try:
        resp = await asyncio.to_thread(_llamar, CONTEXTO_MARCA, prompt, True)
        await update.message.reply_text(_texto(resp)[:3500] or "Sin resultado.")
    except Exception as e:
        await update.message.reply_text(f"No pude analizar la fuente: {e}")


# ------------------------------------------------------------- callbacks / edición
@solo_duena
async def on_boton(update, context):
    q = update.callback_query
    await q.answer()
    accion, bid = q.data.split(":", 1)
    drafts = context.application.bot_data.setdefault("drafts", {})
    b = drafts.get(bid)
    if not b:
        await q.edit_message_reply_markup(None)
        return

    if accion == "ap":
        archivo = APROBADOS / f"{dt.date.today().isoformat()}.md"
        with archivo.open("a", encoding="utf-8") as f:
            f.write(f"\n\n## {b.get('dia','')} · {b.get('pilar','')} — {b.get('angulo','')}\n")
            if b.get("linkedin"):
                f.write(f"\n### LinkedIn\n{b['linkedin']}\n")
            if b.get("threads"):
                f.write(f"\n### Threads\n{b['threads']}\n")
        await q.edit_message_reply_markup(None)
        await q.message.reply_text("✅ Guardado, listo para agendar/pegar.")
    elif accion == "ds":
        drafts.pop(bid, None)
        await q.edit_message_reply_markup(None)
        await q.message.reply_text("🗑️ Descartado.")
    elif accion == "ed":
        context.user_data["editando"] = bid
        await q.message.reply_text("✏️ ¿Qué cambio quieres? Escríbelo y lo reescribo.")


@solo_duena
async def on_texto(update, context):
    bid = context.user_data.get("editando")
    if not bid:
        return
    drafts = context.application.bot_data.setdefault("drafts", {})
    b = drafts.get(bid)
    context.user_data.pop("editando", None)
    if not b:
        return
    await update.message.reply_text("Reescribiendo...")
    nuevo = await asyncio.to_thread(regenerar_uno, b, update.message.text)
    drafts[bid] = nuevo
    await update.message.reply_text(_tarjeta(nuevo), reply_markup=_botones(bid))


# ----------------------------------------------------------------- job semanal
async def job_semanal(context: ContextTypes.DEFAULT_TYPE):
    if dt.date.today().weekday() != 0:      # 0 = lunes
        return
    try:
        borradores = await asyncio.to_thread(generar_lote_semanal)
    except Exception as e:
        log.exception("Error generando lote semanal")
        await context.bot.send_message(CHAT_ID, f"⚠️ No pude generar el lote: {type(e).__name__}: {e}")
        return
    await context.bot.send_message(CHAT_ID, "☀️ Lote de la semana, listo para agendar.")
    await _enviar_lote(context.bot, CHAT_ID, borradores,
                       context.application.bot_data.setdefault("drafts", {}))


def main():
    try:
        import pytz
        tzinfo = pytz.timezone(TZ)
    except Exception:
        tzinfo = None
    builder = Application.builder().token(TELEGRAM_TOKEN)
    if tzinfo is not None:
        builder = builder.defaults(Defaults(tzinfo=tzinfo))
    app = builder.build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("lote", cmd_lote))
    app.add_handler(CommandHandler("semana", cmd_semana))
    app.add_handler(CommandHandler("aprobados", cmd_aprobados))
    app.add_handler(CommandHandler("fuente", cmd_fuente))
    app.add_handler(CallbackQueryHandler(on_boton))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_texto))

    async def on_error(update, context):
        log.exception("Excepción no controlada", exc_info=context.error)
        try:
            await context.bot.send_message(CHAT_ID, f"⚠️ Error interno: {context.error}")
        except Exception:
            pass
    app.add_error_handler(on_error)

    hh, mm = (int(x) for x in POST_TIME.split(":"))
    # La hora se interpreta en la zona fijada arriba (Defaults tzinfo).
    # Corre cada día a la hora fijada, pero solo actúa los lunes (lote semanal).
    app.job_queue.run_daily(job_semanal, time=dt.time(hour=hh, minute=mm))
    log.info("Bot en marcha. Lote semanal los lunes a las %s (%s).", POST_TIME, TZ)
    app.run_polling()


if __name__ == "__main__":
    main()
