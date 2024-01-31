from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, ContextTypes
from credentials import BOT_TOKEN, BOT_USERNAME
import logging
"""import mysql.connector"""
import json

"""mydb = mysql.connector.connect(
    host = 'sql11.freemysqlhosting.net',
    user = 'sql11676026',
    password = 'iiCRnW6sxu',
    database = 'sql11676026',
)
print(mydb)"""
CHAT_IDS = []

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def launch_web_ui(update: Update, callback: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in CHAT_IDS:
        CHAT_IDS.append(user_id)
    kb = [
        [KeyboardButton("Clicca qui!", web_app=WebAppInfo('https://aga19999.github.io/Telegram_bot4/prova.html'))]
    ]
    await update.message.reply_text("Ecco:", reply_markup=ReplyKeyboardMarkup(kb))

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stampa i dati ricevuti e rimuove il bottone"""
    data = json.loads(update.effective_message.web_app_data.data)
    print(data)
    """Qui memorizzo i dati nel DB"""
    """mycursor = mydb.cursor()
    sql = "INSERT INTO utenti (id, nome) VALUES (%s, %s)"
    val = (0, data["nome"])
    mycursor.execute(sql, val)

    mydb.commit()

    print(mycursor.rowcount, "record inserted.")"""

async def help(update: Update, callback: CallbackContext):
    await update.message.reply_text("Questo bot è rivolto al personale scolastico che intende interagire con" +
                                    "gli studenti tramite l'uso di sondaggi e altri widget")

async def web_app_data(update: Update, context: CallbackContext):
    data = json.loads(update.message.web_app_data.data)
    await update.message.reply_text("Your data was:")
    for result in data:
        await update.message.reply_text(f"{result['name']}: {result['value']}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', launch_web_ui))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    print(f"Il bot è in uso! Usalo cliccando qui: http://t.me/{BOT_USERNAME} !")
    application.run_polling()