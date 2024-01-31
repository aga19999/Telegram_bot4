from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, ContextTypes
from credentials import BOT_TOKEN, BOT_USERNAME
import logging
import json
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
    await update.message.reply_text("Iniziamo!", reply_markup=ReplyKeyboardMarkup(kb))

async def help(update: Update, callback: CallbackContext):
    await update.message.reply_text("Questo bot è rivolto al personale scolastico che intende interagire con" +
                                    "gli studenti tramite l'uso di sondaggi e altri widget")

async def web_app_data(update: Update, context: CallbackContext):
    data = json.loads(update.message.web_app_data.data)
    chat_id = update.message.chat_id

    file_name = f"dati_raccolti_{chat_id}.txt"

    with open(file_name, "w") as file:
        file.write(f"Ecco i dati raccolti dalla chat_id {chat_id}:\n")
        for result in data:
            file.write(f"{result['name']}: {result['value']}\n")

    await update.message.reply_text(f"Dati salvati su file: {file_name}")

async def mostra_dati_raccolti(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    file_name = f"dati_raccolti_{chat_id}.txt"

    try:
        with open(file_name, "r") as file:
            content = file.read()
            await update.message.reply_text(f"{content}")
    except FileNotFoundError:
        await update.message.reply_text(f"Nessun dato raccolto per la chat_id {chat_id}.")
    except Exception as e:
        await update.message.reply_text(f"Si è verificato un errore: {str(e)}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', launch_web_ui))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('show_answers', mostra_dati_raccolti))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    """
    Comandi per telegram:
    start - Scopri cosa può fare questo bot!
    help - Chiedi assistenza al bot
    show_answers - Visualizza i risultati
    """

    print(f"Il bot è in uso! Usalo cliccando qui: http://t.me/{BOT_USERNAME} !")
    application.run_polling()