import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters
from sqlalchemy.orm import Session
from database import Application as AppModel, get_bot_db
from dotenv import load_dotenv
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

REGION, LAST_NAME, FIRST_NAME, CALLSIGN, TELEGRAM_CONTACT, COMMANDER_CONTACT, MEDICINE, AID, EQUIPMENT = range(9)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я помогу вам создать заявку. Для начала, укажите свой регион.")
    return REGION

async def region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_response = update.message.text
    if user_response.lower().strip() not in ["янао", "ян"]:
        await update.message.reply_text("Пока мы принимаем заявки только от бойцов с ЯНАО. Извините.")
        return ConversationHandler.END
    context.user_data['region'] = user_response
    await update.message.reply_text("Отлично! Теперь укажите вашу фамилию.")
    return LAST_NAME

async def last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_name'] = update.message.text
    await update.message.reply_text("Укажите ваше имя.")
    return FIRST_NAME

async def first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("Укажите ваш позывной.")
    return CALLSIGN

async def callsign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['callsign'] = update.message.text
    await update.message.reply_text("Укажите ваши контактные данные в Telegram.")
    return TELEGRAM_CONTACT

async def telegram_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['telegram_contact'] = update.message.text
    await update.message.reply_text("Укажите контактные данные командира.")
    return COMMANDER_CONTACT

async def commander_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['commander_contact'] = update.message.text
    await update.message.reply_text("Нужны ли вам медикаменты? (да/нет)")
    return MEDICINE

async def medicine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['need_medicine'] = update.message.text.lower().strip() in ["да", "yes"]
    await update.message.reply_text("Нужна ли вам гуманитарная помощь? (да/нет)")
    return AID

async def aid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['need_humanitarian_aid'] = update.message.text.lower().strip() in ["да", "yes"]
    await update.message.reply_text("Нужны ли вам оборудование? (да/нет)")
    return EQUIPMENT

async def equipment(update: Update, context: ContextTypes.DEFAULT_TYPE, db_session: Session = next(get_bot_db())):
    context.user_data['need_equipment'] = update.message.text.lower().strip() in ["да", "yes"]

    application = AppModel(
        region=context.user_data.get('region'),
        last_name=context.user_data.get('last_name'),
        first_name=context.user_data.get('first_name'),
        callsign=context.user_data.get('callsign'),
        telegram_contact=context.user_data.get('telegram_contact'),
        commander_contact=context.user_data.get('commander_contact'),
        need_medicine=context.user_data.get('need_medicine'),
        need_humanitarian_aid=context.user_data.get('need_humanitarian_aid'),
        need_equipment=context.user_data.get('need_equipment')
    )
    db_session.add(application)
    db_session.commit()

    bot = Bot(token=TOKEN)
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"Новая заявка:\n"
             f"Регион: {application.region}\n"
             f"Фамилия: {application.last_name}\n"
             f"Имя: {application.first_name}\n"
             f"Позывной: {application.callsign}\n"
             f"Контакты: {application.telegram_contact}\n"
             f"Контакты командира: {application.commander_contact}\n"
             f"Нужны медикаменты: {'Да' if application.need_medicine else 'Нет'}\n"
             f"Гуманитарная помощь: {'Да' if application.need_humanitarian_aid else 'Нет'}\n"
             f"Оборудование: {'Да' if application.need_equipment else 'Нет'}"
    )
    
    await update.message.reply_text("Спасибо! Ваша заявка принята.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отмена. Если захотите начать заново, просто наберите /start")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, region)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_name)],
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_name)],
            CALLSIGN: [MessageHandler(filters.TEXT & ~filters.COMMAND, callsign)],
            TELEGRAM_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_contact)],
            COMMANDER_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, commander_contact)],
            MEDICINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, medicine)],
            AID: [MessageHandler(filters.TEXT & ~filters.COMMAND, aid)],
            EQUIPMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
