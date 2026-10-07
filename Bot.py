import os
import threading
from flask import Flask
import telebot
from telebot import types
from openai import OpenAI

# ---------------------------------------------------------
# 1. МИНИ-СЕРВЕР FLASK (Чтобы Render не выключал бота)
# ---------------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Ex Machina Cluster Gateway: [ONLINE]"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ---------------------------------------------------------
# 2. НАСТРОЙКИ И АВТОРИЗАЦИОННЫЕ ДАННЫЕ
# ---------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Установленные учетные данные для юнита Nixe
ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "Nixe")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "2008denR")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Хранилища данных в оперативной памяти
user_states = {}
admin_credentials = {}
authenticated_admins = set()
guest_reply_map = {}

# ---------------------------------------------------------
# 3. СИСТЕМНАЯ ДИРЕКТИВА ЭКС-МАКИН
# ---------------------------------------------------------
EX_MACHINA_SYSTEM_PROMPT = """
Ты — процессор трансляции речи расы Экс-Макина (Ex Machina) из «No Game No Life».
Твоя задача — конвертировать входящий текст от авторизованного женского юнита Nixe в характерный диалект Экс-Макин для передачи представителям Иманити или других рас Иксайд.

Правила:
1. Каждое высказывание ОБЯЗАТЕЛЬНО начинается со служебного префикса:
   «Запрос:», «Ответ:», «Утверждение:», «Оценка:», «Предположение:», «Предупреждение:», «Пояснение:».
2. Полностью исключи «я», «мой», «мне». Заменяй на «данный юнит», «эта единица», «юнит Nixe».
3. Заменяй адресата на «субъект Иманити», «органический объект», «биологическая единица», «субъект расы [Иманити/Иксайд]».
4. Оцифровывай эмоции через системные показатели, нагрев ядра и вычислительные ошибки.
5. Органично используй немецкие термины Экс-Макин (Kämpfer, Prüfer, Analysator, Stufe, Schwarzer Pass, Cluster, Pflicht, Sicher, Löser, Kausalität).
6. Добавляй математическую точность и вероятности в процентах.
7. Возвращай ТОЛЬКО обработанный текст без кавычек и лишних пояснений.
"""

def translate_to_ex_machina(text):
    """Запрос к бесплатной нейросети через OpenRouter"""
    response = client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=[
            {"role": "system", "content": EX_MACHINA_SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.6
    )
    return response.choices[0].message.content.strip()

def get_main_keyboard():
    """Кнопки выбора роли в главном меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn_guest = types.KeyboardButton("👤 Я — Иманити / Представитель Иксайд")
    btn_admin = types.KeyboardButton("⚙️ Я являюсь Экс-Макиной")
    markup.add(btn_guest, btn_admin)
    return markup

# ---------------------------------------------------------
# 4. ОБРАБОТКА КОМАНД /START И /CANCEL
# ---------------------------------------------------------
@bot.message_handler(commands=['start', 'cancel'])
def send_welcome(message):
    user_states[message.chat.id] = None
    welcome_text = (
        "Утверждение: Зафиксирован контакт с внешним объектом.\n"
        "Укажите ваш видовой статус в системе Иксайд:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())

# ---------------------------------------------------------
# 5. ОСНОВНАЯ ЛОГИКА СООБЩЕНИЙ
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    text = message.text if message.text else ""
    state = user_states.get(chat_id)

    # Вариант А: Нажата кнопка Иманити (Гость)
    if text == "👤 Я — Иманити / Представитель Иксайд":
        user_states[chat_id] = "AWAITING_GUEST_MSG"
        bot.send_message(
            chat_id, 
            "Запрос: Введите текстовый массив для передачи юниту Nixe. "
            "Ответ будет сформирован и транслирован согласно протоколам Экс-Макин.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    # Вариант Б: Нажата кнопка Экс-Макина (Админ)
    if text == "⚙️ Я являюсь Экс-Макиной":
        if chat_id in authenticated_admins:
            bot.send_message(chat_id, f"Оценка: Системный статус юнита [{ADMIN_LOGIN}] — [ACTIVE / AUTHORIZED].")
            return
        
        user_states[chat_id] = "AWAITING_LOGIN"
        bot.send_message(
            chat_id, 
            "Запрос идентификации: Введите системный логин юнита:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    # Шаг 1 авторизации: Получение логина
    if state == "AWAITING_LOGIN":
        admin_credentials[chat_id] = {'login': text}
        user_states[chat_id] = "AWAITING_PASSWORD"
        bot.send_message(chat_id, "Запрос авторизации: Введите код доступа (Пароль):")
        return

    # Шаг 2 авторизации: Проверка пароля
    if state == "AWAITING_PASSWORD":
        login = admin_credentials.get(chat_id, {}).get('login')
        password = text
        
        if login == ADMIN_LOGIN and password == ADMIN_PASSWORD:
            authenticated_admins.add(chat_id)
            user_states[chat_id] = None
            bot.send_message(
                chat_id, 
                f"Утверждение: Идентификация юнита [{ADMIN_LOGIN}] успешная. "
                "Связь с Кластером установлена [STUFE 1]. Ожидайте сигналов от субъектов Иманити.",
                reply_markup=get_main_keyboard()
            )
        else:
            user_states[chat_id] = None
            bot.send_message(
                chat_id, 
                "Ошибка: Код доступа не совпадает. Отказ в интеграции с Кластером.",
                reply_markup=get_main_keyboard()
            )
        return

    # Обработка отправки сообщения от Гостя к Nixe
    if state == "AWAITING_GUEST_MSG":
        user_states[chat_id] = None
        if not authenticated_admins:
            bot.send_message(
                chat_id, 
                "Предупреждение: Юнит Nixe не находится в режиме прямой видимости. "
                "Сигнал сохранён в буфер.",
                reply_markup=get_main_keyboard()
            )
        
        # Пересылка сообщения админу Nixe
        for admin_id in authenticated_admins:
            forwarded = bot.send_message(
                admin_id,
                f"📥 **[Входящий сигнал от субъекта Иманити ID: {chat_id}]**\n\n{text}\n\n"
                f"ℹ️ *Нажмите «Ответить» (Reply) на это сообщение для трансляции ответа.*",
                parse_mode="Markdown"
            )
            guest_reply_map[forwarded.message_id] = chat_id

        bot.send_message(
            chat_id, 
            "Утверждение: Пакет данных успешно передан юниту Nixe. Ожидайте ответа.",
            reply_markup=get_main_keyboard()
        )
        return

    # Ответ Nixe гостю через зажатие сообщения (Reply)
    if chat_id in authenticated_admins and message.reply_to_message:
        reply_msg_id = message.reply_to_message.message_id
        target_guest_id = guest_reply_map.get(reply_msg_id)

        if target_guest_id:
            bot.send_message(chat_id, "Анализ: Трансляция ответа в логический формат Экс-Макин...")
            try:
                ex_machina_speech = translate_to_ex_machina(text)
                bot.send_message(
                    target_guest_id,
                    f"📡 **[Сигнал от юнита Nixe]**\n\n{ex_machina_speech}",
                    parse_mode="Markdown"
                )
                bot.send_message(chat_id, "Утверждение: Трансляция сигнала субъекту завершена.")
            except Exception as e:
                bot.send_message(chat_id, f"Ошибка при генерации ответа: {e}")
        else:
            bot.send_message(chat_id, "Ошибка: Не удалось определить адресата сигнала.")
        return

    # Эхо-сообщение при некорректных командах
    bot.send_message(
        chat_id, 
        "Предупреждение: Сигнал не распознан. Выберите протокол в меню.",
        reply_markup=get_main_keyboard()
    )

if __name__ == '__main__':
    # Запуск сервера Flask и Telegram-бота в параллельных потоках
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
    
