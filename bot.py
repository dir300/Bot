import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# === НАСТРОЙКИ (все в .env) ===
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")  # например: "@your_manager_bot" или "https://t.me/username"

if not TOKEN or not ADMIN_ID:
    raise ValueError("TOKEN или ADMIN_ID не заданы в .env!")

# ДАННЫЕ ВАКАНСИИ (настройте под себя)
VACANCY_TITLE = "Менеджер по продажам"
VACANCY_SALARY = "от 80 000 до 150 000 ₽"
VACANCY_SCHEDULE = "Полный день, с 9:00 до 18:00"
VACANCY_LOCATION = "Москва, м. Курская (гибрид)"
VACANCY_REQUIREMENTS = (
    "• Опыт в продажах от 1 года\n"
    "• Коммуникабельность\n"
    "• Готовность к активным продажам"
)
VACANCY_BENEFITS = (
    "• Белая зарплата + бонусы\n"
    "• Обучение за счёт компании\n"
    "• Корпоративные мероприятия"
)
VACANCY_CONTACT = "📩 По вопросам: @your_support_bot или +7 (XXX) XXX-XX-XX"

# FAQ (можно расширять)
FAQ = {
    "зарплата": f"Зарплата: {VACANCY_SALARY}. Выплачивается 2 раза в месяц.",
    "график": f"График работы: {VACANCY_SCHEDULE}.",
    "место": f"Место: {VACANCY_LOCATION}.",
    "требования": f"Требования:\n{VACANCY_REQUIREMENTS}",
    "льготы": f"Мы предлагаем:\n{VACANCY_BENEFITS}",
}

# Состояния для диалога
NAME, CONTACT, RESUME = range(3)

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# === КНОПКА "СВЯЗАТЬСЯ С МЕНЕДЖЕРОМ" ===
def get_manager_button():
    if MANAGER_CHAT_ID:
        return [[InlineKeyboardButton("💬 Связаться с менеджером", url=MANAGER_CHAT_ID)]]
    return []

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📌 О вакансии", callback_data="vacancy")],
        [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")],
        [InlineKeyboardButton("📤 Оставить отклик", callback_data="apply")],
    ]
    # Добавляем кнопку менеджера, если указана
    keyboard += get_manager_button()
    return InlineKeyboardMarkup(keyboard)

def get_back_to_start_button():
    buttons = [[InlineKeyboardButton("🔙 В главное меню", callback_data="start")]]
    buttons += get_manager_button()
    return InlineKeyboardMarkup(buttons)

# === КОМАНДЫ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Привет! 👋\n\nВы рассматриваете вакансию:\n\n*{VACANCY_TITLE}*\n\nВыберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# Показ вакансии
async def show_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        f"*{VACANCY_TITLE}*\n\n"
        f"💰 *Зарплата:* {VACANCY_SALARY}\n"
        f"📅 *График:* {VACANCY_SCHEDULE}\n"
        f"📍 *Место:* {VACANCY_LOCATION}\n\n"
        f"✅ *Требования:*\n{VACANCY_REQUIREMENTS}\n\n"
        f"🎁 *Льготы и бонусы:*\n{VACANCY_BENEFITS}\n\n"
        f"📞 *Контакт:* {VACANCY_CONTACT}"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=get_back_to_start_button(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=get_back_to_start_button(),
            parse_mode="Markdown"
        )

# Показ FAQ
async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Зарплата", callback_data="faq_salary")],
        [InlineKeyboardButton("📅 График", callback_data="faq_schedule")],
        [InlineKeyboardButton("📍 Место", callback_data="faq_location")],
        [InlineKeyboardButton("✅ Требования", callback_data="faq_requirements")],
        [InlineKeyboardButton("🎁 Льготы", callback_data="faq_benefits")],
    ]
    keyboard += get_manager_button()
    keyboard += [[InlineKeyboardButton("🔙 В главное меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Выберите интересующий вопрос:", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Выберите интересующий вопрос:", reply_markup=reply_markup)

# Обработка FAQ
async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.replace("faq_", "")

    mapping = {
        "salary": "зарплата",
        "schedule": "график",
        "location": "место",
        "requirements": "требования",
        "benefits": "льготы"
    }
    key = mapping.get(data)
    answer = FAQ.get(key, "Вопрос не найден.")

    keyboard = [[InlineKeyboardButton("🔙 Назад к FAQ", callback_data="faq")]]
    keyboard += get_manager_button()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(answer, reply_markup=reply_markup)

# Начало отклика
async def start_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        "Пожалуйста, введите ваше *полное имя*:",
        parse_mode="Markdown",
        reply_markup=get_back_to_start_button()
    )
    return NAME

# Получение имени
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        "Отлично! Теперь введите контакт (Telegram, WhatsApp или телефон):",
        reply_markup=get_back_to_start_button()
    )
    return CONTACT

# Получение контакта
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text
    await update.message.reply_text(
        "Прикрепите ваше резюме (файл PDF или DOC):",
        reply_markup=get_back_to_start_button()
    )
    return RESUME

# Получение резюме и отправка админу
async def get_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    name = context.user_data["name"]
    contact = context.user_data["contact"]

    if update.message.document:
        file = update.message.document
        file_id = file.file_id
        file_name = file.file_name
    elif update.message.text and not update.message.text.startswith("/"):
        file_id = None
        file_name = "(текст вместо файла)"
    else:
        file_id = None
        file_name = "(нет файла)"

    # Отправка админу
    message_to_admin = (
        f"📬 *Новый отклик на вакансию*\n\n"
        f"👤 *Имя:* {name}\n"
        f"📞 *Контакт:* {contact}\n"
        f"📎 *Файл:* {file_name}\n"
        f"🆔 *ID пользователя:* {user.id}\n"
        f"🌐 *Username:* @{user.username or 'нет'}"
    )

    try:
        if file_id:
            await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=file_id,
                caption=message_to_admin,
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=message_to_admin,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="❌ Ошибка: не удалось отправить отклик."
        )

    # Подтверждение пользователю
    await update.message.reply_text(
        "✅ *Спасибо за отклик!* Мы свяжемся с вами в ближайшее время.\n\n"
        "Если у вас остались вопросы — задавайте!",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

# Возврат в меню
async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# === ОСНОВНОЙ ЗАПУСК ===
def main():
    application = Application.builder().token(TOKEN).build()

    # Обработчик диалога отклика
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_apply, pattern="apply")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            RESUME: [
                MessageHandler(
                    filters.Document.ALL | (filters.TEXT & ~filters.COMMAND),
                    get_resume
                )
            ],
        },
        fallbacks=[CallbackQueryHandler(back_to_start, pattern="start")],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_vacancy, pattern="vacancy"))
    application.add_handler(CallbackQueryHandler(show_faq, pattern="faq"))
    application.add_handler(CallbackQueryHandler(handle_faq, pattern="^faq_"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="start"))
    application.add_handler(conv_handler)

    # Запуск
    application.run_polling()
    print("Бот запущен...")

if __name__ == "__main__":
    main()