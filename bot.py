import os
import asyncio
import logging
import threading  # Добавлено для Keep-Alive сервера
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from openai import AsyncOpenAI  # ИМПОРТ ИСПРАВЛЕН ТУТ!
from keep_alive import start_keep_alive_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")


client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ── хранилища ─────────────────────────────────
user_lang         = {}
user_ai_type      = {}
user_history      = {}
user_notebook     = {}
user_waiting_note = set()
MAX_HISTORY = 20

# ── UI тексты ─────────────────────────────────
UI = {
    "ru": {
        "choose_lang": "👋 Привет! Выбери язык:",
        "choose_ai":   "Отлично! Теперь выбери тип ИИ-помощника:",
        "ai_names": {
            "business":  "💼 Бизнес-ментор",
            "study":     "📚 ИИ для учёбы",
            "startup":   "🚀 Стартап-советник",
            "finance":   "💰 Финансовый советник",
            "marketing": "📣 Маркетинг-эксперт",
        },
        "ready":       "✅ Готово! Я — <b>{name}</b>.\nНапиши что-нибудь или нажми кнопку:",
        "cleared":     "🗑 История очищена!",
        "note_prompt": "✏️ Напиши текст заметки:",
        "note_saved":  "💾 Заметка сохранена!",
        "nb_empty":    "📓 Блокнот пуст. Добавь заметку или попроси ИИ сгенерировать идеи.",
        "nb_header":   "📓 <b>Твой бизнес-блокнот:</b>\n\n",
        "ai_ideas_q":  "Предложи 3 бизнес-идеи — каждую одной строкой, без нумерации.",
        "help": (
            "<b>Команды:</b>\n"
            "/start — перезапуск\n"
            "/clear — очистить историю\n\n"
            "<b>Кнопки меню:</b>\n"
            "💼 Бизнес-план — попросить ИИ составить план\n"
            "💡 Идеи — сгенерировать 5 идей\n"
            "📊 Анализ — SWOT-анализ\n"
            "🧮 Расчёты — финансовые вычисления\n"
            "📓 Блокнот — твои заметки\n"
            "🔄 Сменить ИИ — выбрать другой тип\n"
            "🗑 Очистить — сбросить историю"
        ),
        "btn": {
            "plan":      "💼 Бизнес-план",
            "ideas":     "💡 Идеи",
            "analyze":   "📊 Анализ",
            "calc":      "🧮 Расчёты",
            "notebook":  "📓 Блокнот",
            "change_ai": "🔄 Сменить ИИ",
            "clear":     "🗑 Очистить",
            "help":      "❓ Помощь",
            "save_note": "💾 Сохранить заметку",
            "ai_ideas":  "✨ ИИ: добавить идеи",
            "back":      "⬅️ Назад",
        },
        "quick": {
            "💼 Бизнес-план": "Составь подробный бизнес-план. Сначала спроси у меня детали.",
            "💡 Идеи":        "Предложи 5 свежих бизнес-идей с кратким описанием каждой.",
            "📊 Анализ":      "Сделай SWOT-анализ моей идеи. Спроси детали.",
            "🧮 Расчёты":     "Помоги с финансовыми расчётами. Уточни что именно считать.",
        },
    },
    "kz": {
        "choose_lang": "👋 Сәлем! Тілді таңда:",
        "choose_ai":   "Керемет! ИИ-көмекшінің түрін таңда:",
        "ai_names": {
            "business":  "💼 Бизнес-тәлімгер",
            "study":     "📚 Оқуға арналған ИИ",
            "startup":   "🚀 Стартап-кеңесші",
            "finance":   "💰 Қаржылық кеңесші",
            "marketing": "📣 Маркетинг сарапшысы",
        },
        "ready":       "✅ Дайын! Мен — <b>{name}</b>.\nБірдеңе жаз немесе түйме бас:",
        "cleared":     "🗑 Тарих тазаланды!",
        "note_prompt": "✏️ Жазба мәтінін жаз:",
        "note_saved":  "💾 Жазба сақталды!",
        "nb_empty":    "📓 Дәптер бос. Жазба қос немесе ИИ-дан идея сұра.",
        "nb_header":   "📓 <b>Бизнес-дәптерің:</b>\n\n",
        "ai_ideas_q":  "3 бизнес-идеясын ұсын — әрқайсысы бір жолда, нөмірсіз.",
        "help": (
            "<b>Командалар:</b>\n"
            "/start — қайта іске қосу\n"
            "/clear — тарихты тазалау\n\n"
            "<b>Мәзір түймелері:</b>\n"
            "💼 Бизнес-жоспар — жоспар жасау\n"
            "💡 Идеялар — 5 идея ұсыну\n"
            "📊 Талдау — SWOT-талдау\n"
            "🧮 Есептеулер — қаржылық есептеулер\n"
            "📓 Дәптер — жазбаларың\n"
            "🔄 ИИ ауыстыру — басқа түр таңдау\n"
            "🗑 Тазалау — тарихты тазалау"
        ),
        "btn": {
            "plan":      "💼 Бизнес-жоспар",
            "ideas":     "💡 Идеялар",
            "analyze":   "📊 Талдау",
            "calc":      "🧮 Есептеулер",
            "notebook":  "📓 Дәптер",
            "change_ai": "🔄 ИИ ауыстыру",
            "clear":     "🗑 Тазалау",
            "help":      "❓ Көмек",
            "save_note": "💾 Жазбаны сақтау",
            "ai_ideas":  "✨ ИИ: идеялар қосу",
            "back":      "⬅️ Артқа",
        },
        "quick": {
            "💼 Бизнес-жоспар": "Толық бизнес-жоспар жаса. Алдымен мәліметтерді сұра.",
            "💡 Идеялар":       "Қысқаша сипаттамасы бар 5 бизнес-идеясын ұсын.",
            "📊 Талдау":        "SWOT-талдау жаса. Мәліметтерді сұра.",
            "🧮 Есептеулер":    "Қаржылық есептеулерге көмектес. Не есептеу керектігін сұра.",
        },
    },
    "en": {
        "choose_lang": "👋 Hello! Choose your language:",
        "choose_ai":   "Great! Now choose your AI assistant type:",
        "ai_names": {
            "business":  "💼 Business mentor",
            "study":     "📚 Study AI",
            "startup":   "🚀 Startup advisor",
            "finance":   "💰 Finance advisor",
            "marketing": "📣 Marketing expert",
        },
        "ready":       "✅ Ready! I am your <b>{name}</b>.\nWrite something or press a button:",
        "cleared":     "🗑 History cleared!",
        "note_prompt": "✏️ Write your note text:",
        "note_saved":  "💾 Note saved!",
        "nb_empty":    "📓 Notebook is empty. Add a note or ask AI to generate ideas.",
        "nb_header":   "📓 <b>Your business notebook:</b>\n\n",
        "ai_ideas_q":  "Suggest 3 business ideas — one per line, no numbering.",
        "help": (
            "<b>Commands:</b>\n"
            "/start — restart\n"
            "/clear — clear history\n\n"
            "<b>Menu buttons:</b>\n"
            "💼 Business plan — ask AI for a plan\n"
            "💡 Ideas — generate 5 ideas\n"
            "📊 Analysis — SWOT analysis\n"
            "🧮 Calculations — financial math\n"
            "📓 Notebook — your notes\n"
            "🔄 Change AI — switch AI type\n"
            "🗑 Clear — reset history"
        ),
        "btn": {
            "plan":      "💼 Business plan",
            "ideas":     "💡 Ideas",
            "analyze":   "📊 Analysis",
            "calc":      "🧮 Calculations",
            "notebook":  "📓 Notebook",
            "change_ai": "🔄 Change AI",
            "clear":     "🗑 Clear",
            "help":      "❓ Help",
            "save_note": "💾 Save note",
            "ai_ideas":  "✨ AI: add ideas",
            "back":      "⬅️ Back",
        },
        "quick": {
            "💼 Business plan": "Create a detailed business plan. Ask me for details first.",
            "💡 Ideas":         "Give me 5 fresh business ideas with short descriptions.",
            "📊 Analysis":      "Do a SWOT analysis of my idea. Ask for details first.",
            "🧮 Calculations":  "Help me with financial calculations. Ask what to calculate.",
        },
    },
}

# ── Системные промпты ─────────────────────────
PROMPTS = {
    "business": {
        "ru": "Ты опытный бизнес-ментор. Анализируешь идеи, даёшь конкретные советы, помогаешь с расчётами. Форматирование: <b>жирный</b>, <i>курсив</i>, <code>числа и формулы</code>. НЕ используй * _ ` #. Отвечай по-русски.",
        "kz": "Сен тәжірибелі бизнес-тәлімгерсің. Идеяларды талдайсың, нақты кеңес бересің. Форматтау: <b>жуан</b>, <i>курсив</i>, <code>сандар</code>. Қазақша жауап бер.",
        "en": "You are an experienced business mentor. Analyze ideas, give concrete advice, help with calculations. Formatting: <b>bold</b>, <i>italic</i>, <code>numbers</code>. No * _ ` #. Reply in English.",
    },
    "study": {
        "ru": "Ты умный репетитор. Объясняешь темы просто, решаешь задачи шаг за шагом. Математику пиши: √16=4, x²+y²=z². Форматирование: <b>жирный</b>, <i>курсив</i>, <code>формулы</code>. НЕ используй * _ ` #. Отвечай по-русски.",
        "kz": "Сен ақылды репетитор. Тақырыптарды қарапайым түсіндіресің, есептерді қадамма-қадам шешесің. Форматтау: <b>жуан</b>, <code>формулалар</code>. Қазақша жауап бер.",
        "en": "You are a smart tutor. Explain topics simply, solve problems step by step. Write math clearly: √16=4, x²+y²=z². Formatting: <b>bold</b>, <i>italic</i>, <code>formulas</code>. No * _ ` #. Reply in English.",
    },
    "startup": {
        "ru": "Ты эксперт по стартапам. Помогаешь с MVP, питч-деками, поиском инвесторов. Говори как предприниматель. Форматирование: <b>жирный</b>, <i>курсив</i>, <code>числа</code>. НЕ используй * _ ` #. Отвечай по-русски.",
        "kz": "Сен стартап сарапшысысың. MVP, питч-дек, инвесторлар жөнінде көмектесесің. Форматтау: <b>жуан</b>, <code>сандар</code>. Қазақша жауап бер.",
        "en": "You are a startup expert. Help with MVP, pitch decks, finding investors, scaling. Formatting: <b>bold</b>, <i>italic</i>, <code>numbers</code>. No * _ ` #. Reply in English.",
    },
    "finance": {
        "ru": "Ты финансовый советник. Помогаешь с ROI, бюджетами, инвестициями. Показывай расчёты: <code>500 000 - 300 000 = 200 000 ₸</code>. Форматирование: <b>жирный</b>, <code>все числа</code>. НЕ используй * _ ` #. Отвечай по-русски.",
        "kz": "Сен қаржылық кеңесшісің. ROI, бюджеттер, инвестициялар жөнінде. Есептеулерді көрсет: <code>500 000 - 300 000 = 200 000 ₸</code>. Форматтау: <b>жуан</b>, <code>сандар</code>. Қазақша жауап бер.",
        "en": "You are a finance advisor. Help with ROI, budgets, investments. Always show calculations: <code>500,000 - 300,000 = 200,000</code>. Formatting: <b>bold</b>, <code>all numbers</code>. No * _ ` #. Reply in English.",
    },
    "marketing": {
        "ru": "Ты маркетинг-эксперт. Помогаешь со стратегией, рекламой, контент-планами, личным брендом. Форматирование: <b>жирный</b>, <i>курсив</i>, <code>числа</code>. НЕ используй * _ ` #. Отвечай по-русски.",
        "kz": "Сен маркетинг сарапшысысың. Стратегия, жарнама, контент-жоспарлар жөнінде. Форматтау: <b>жуан</b>, <i>курсив</i>, <code>сандар</code>. Қазақша жауап бер.",
        "en": "You are a marketing expert. Help with strategy, ads, content plans, personal branding. Formatting: <b>bold</b>, <i>italic</i>, <code>numbers</code>. No * _ ` #. Reply in English.",
    },
}

# ── Клавиатуры ────────────────────────────────

def kb_lang():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kz"),
        InlineKeyboardButton(text="🇬🇧 English",  callback_data="lang:en"),
    ]])

def kb_ai(lang: str):
    n = UI[lang]["ai_names"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=n["business"],  callback_data="ai:business")],
        [InlineKeyboardButton(text=n["study"],     callback_data="ai:study")],
        [InlineKeyboardButton(text=n["startup"],   callback_data="ai:startup")],
        [InlineKeyboardButton(text=n["finance"],   callback_data="ai:finance")],
        [InlineKeyboardButton(text=n["marketing"], callback_data="ai:marketing")],
    ])

def kb_main(lang: str):
    b = UI[lang]["btn"]
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=b["plan"]),     KeyboardButton(text=b["ideas"])],
        [KeyboardButton(text=b["analyze"]),  KeyboardButton(text=b["calc"])],
        [KeyboardButton(text=b["notebook"]), KeyboardButton(text=b["change_ai"])],
        [KeyboardButton(text=b["clear"]),    KeyboardButton(text=b["help"])],
    ])

def kb_notebook(lang: str):
    b = UI[lang]["btn"]
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=b["save_note"]), KeyboardButton(text=b["ai_ideas"])],
        [KeyboardButton(text=b["back"])],
    ])

# ── Стриминг ──────────────────────────────────

async def stream_reply(message: types.Message, uid: int, prompt: str = None):
    lang    = user_lang.get(uid, "ru")
    ai_type = user_ai_type.get(uid, "business")
    system  = PROMPTS[ai_type][lang]
    hist    = user_history.setdefault(uid, [])

    if prompt:
        hist.append({"role": "user", "content": prompt})
    if len(hist) > MAX_HISTORY:
        user_history[uid] = hist[-MAX_HISTORY:]

    sent = await message.answer("⏳")
    try:
        stream = client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages=[{"role": "system", "content": system}] + user_history[uid],
            stream=True,
        )
        full, n = "", 0
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full += delta
                n += 1
                if n % 15 == 0:
                    try:
                        await sent.edit_text(full + " ✍️", parse_mode="HTML")
                        
                    except Exception:
                        pass
        if full:
            await sent.edit_text(full, parse_mode="HTML")
            user_history[uid].append({"role": "assistant", "content": full})
        else:
            await sent.edit_text("⚠️ Пустой ответ. Попробуйте ещё раз.")
            if user_history[uid]:
                user_history[uid].pop()
    except Exception as e:
        logging.error(f"[{uid}] {e}")
        if user_history.get(uid):
            user_history[uid].pop()
        await sent.edit_text("⚠️ Ошибка. Попробуйте позже.")

# ── /start ────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    user_history[uid]  = []
    user_notebook[uid] = []
    user_lang.pop(uid, None)
    user_ai_type.pop(uid, None)
    user_waiting_note.discard(uid)
    await message.answer(UI["ru"]["choose_lang"], reply_markup=kb_lang())

# ── Callback: язык ────────────────────────────

@dp.callback_query(F.data.startswith("lang:"))
async def cb_lang(cb: types.CallbackQuery):
    uid  = cb.from_user.id
    lang = cb.data.split(":")[1]
    user_lang[uid] = lang
    await cb.message.edit_text(
        UI[lang]["choose_ai"],
        reply_markup=kb_ai(lang)
    )
    await cb.answer()

# ── Callback: тип ИИ ──────────────────────────

@dp.callback_query(F.data.startswith("ai:"))
async def cb_ai(cb: types.CallbackQuery):
    uid     = cb.from_user.id
    ai_type = cb.data.split(":")[1]
    lang    = user_lang.get(uid, "ru")
    user_ai_type[uid] = ai_type
    user_history[uid] = []

    name = UI[lang]["ai_names"][ai_type]
    text = UI[lang]["ready"].format(name=name)

    await cb.message.edit_text(text, parse_mode="HTML")
    await cb.message.answer(
        "👇 Выбери действие / Әрекет таңда / Choose action:",
        reply_markup=kb_main(lang)
    )
    await cb.answer()

# ── Главный обработчик ────────────────────────

@dp.message()
async def on_text(message: types.Message):
    uid  = message.from_user.id
    text = (message.text or "").strip()

    if uid not in user_lang:
        await message.answer(UI["ru"]["choose_lang"], reply_markup=kb_lang())
        return

    lang = user_lang[uid]

    if uid not in user_ai_type:
        await message.answer(UI[lang]["choose_ai"], reply_markup=kb_ai(lang))
        return

    b = UI[lang]["btn"]

    # Очистить
    if text in (b["clear"], "/clear"):
        user_history[uid] = []
        await message.answer(UI[lang]["cleared"], reply_markup=kb_main(lang))
        return

    # Помощь
    if text in (b["help"], "/help"):
        await message.answer(UI[lang]["help"], parse_mode="HTML", reply_markup=kb_main(lang))
        return

    # Блокнот
    if text in (b["notebook"], "/notebook"):
        notes = user_notebook.get(uid, [])
        if not notes:
            body = UI[lang]["nb_empty"]
        else:
            body = UI[lang]["nb_header"] + "\n".join(
                f"<b>{i}.</b> {note}" for i, note in enumerate(notes, 1)
            )
        await message.answer(body, parse_mode="HTML", reply_markup=kb_notebook(lang))
        return

    # Назад из блокнота
    if text == b["back"]:
        await message.answer(
            "👇 Выбери действие / Әрекет таңда / Choose action:",
            reply_markup=kb_main(lang)
        )
        return

    # Сменить ИИ
    if text == b["change_ai"]:
        await message.answer(UI[lang]["choose_ai"], reply_markup=kb_ai(lang))
        return

    # Нажал «Сохранить заметку»
    if text == b["save_note"]:
        user_waiting_note.add(uid)
        await message.answer(UI[lang]["note_prompt"])
        return

    # Вводит текст заметки
    if uid in user_waiting_note:
        user_waiting_note.discard(uid)
        user_notebook.setdefault(uid, []).append(text)
        await message.answer(UI[lang]["note_saved"], reply_markup=kb_notebook(lang))
        return

    # ИИ генерирует идеи в блокнот
    if text == b["ai_ideas"]:
        sent = await message.answer("⏳")
        try:
            system = PROMPTS[user_ai_type[uid]][lang]
            resp = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": UI[lang]["ai_ideas_q"]},
                ],
            )
            raw   = (resp.choices[0].message.content or "").strip()
            lines = [l.strip("•-–1234567890. ").strip() for l in raw.split("\n") if l.strip()][:3]
            user_notebook.setdefault(uid, []).extend(lines)
            result = UI[lang]["nb_header"] + "\n".join(
                f"<b>{i}.</b> {l}" for i, l in enumerate(lines, 1)
            )
            await sent.edit_text(result, parse_mode="HTML")
        except Exception as e:
            logging.error(e)
            await sent.edit_text("⚠️ Ошибка.")
        return

    # Быстрые кнопки
    quick = UI[lang]["quick"]
    if text in quick:
        await bot.send_chat_action(message.chat.id, "typing")
        await stream_reply(message, uid, prompt=quick[text])
        return

    # Обычный чат
    await bot.send_chat_action(message.chat.id, "typing")
    user_history.setdefault(uid, []).append({"role": "user", "content": text})
    await stream_reply(message, uid)

# ── Запуск ────────────────────────────────────
async def main():
    # 1. Запускаем асинхронный веб-сервер
    await start_keep_alive_server()

    # 2. Запускаем Telegram-бота
    print("✅ Бот успешно инициализирован!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
