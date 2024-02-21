from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, ContextTypes
from credentials import BOT_TOKEN, BOT_USERNAME, PASSWORD_DATABASE
import pymysql.cursors
import json

USER_IDS = []
connection = pymysql.connect(host='localhost',
                             user='root',
                             password=PASSWORD_DATABASE,
                             database='telegramBot',
                             cursorclass=pymysql.cursors.DictCursor)

async def launch_web_ui(update: Update, callback: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in USER_IDS:
        USER_IDS.append(user_id)
    kb = [
        [KeyboardButton("Clicca qui!", web_app=WebAppInfo('https://aga19999.github.io/Telegram_bot4/prova.html'))]
    ]
    await update.message.reply_text("Iniziamo!", reply_markup=ReplyKeyboardMarkup(kb))

async def help(update: Update, callback: CallbackContext):
    await update.message.reply_text("Questo bot è rivolto al personale scolastico che intende interagire con" +
                                    "gli studenti tramite l'uso di sondaggi e altri widget")

async def web_app_data(update: Update, context: CallbackContext):
    data = json.loads(update.message.web_app_data.data)
    user_id = update.message.from_user.id

    connection = pymysql.connect(
        host='localhost',
        user='root',
        password=PASSWORD_DATABASE,
        database='telegramBot',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            id_domanda = 1000
            for result in data:
                sql = "INSERT INTO rilevazioni (id_domanda, risposta, id_utente) VALUES (%s, %s, %s)"
                cursor.execute(sql, (id_domanda, result['value'], user_id))
                id_domanda += 1

        connection.commit()

        await update.message.reply_text("Dati salvati nel database con successo!")
    except Exception as e:
        await update.message.reply_text(f"Si è verificato un errore durante il salvataggio nel database: {str(e)}")
    finally:
        connection.close()

async def mostra_dati_raccolti(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    connection2 = pymysql.connect(
        host='localhost',
        user='root',
        password=PASSWORD_DATABASE,
        database='telegramBot',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection2.cursor() as cursor:

            # Esegui la query per recuperare i dati dal database
            sql = "SELECT * FROM rilevazioni WHERE id_utente=%s"
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()

            if results:
                content = "\n".join([f"{result['Id_domanda']}: {result['Risposta']}" for result in results])
                await update.message.reply_text(f"Ecco i dati raccolti dalla chat_id {user_id}:\n\n{content}")
            else:
                await update.message.reply_text(f"Nessun dato raccolto per la chat_id {user_id}.")
    except Exception as e:
        await update.message.reply_text(
            f"Si è verificato un errore durante il recupero dei dati dal database: {str(e)}")
    finally:
        connection2.close()


if __name__ == '__main__':
    print(f"Il bot è in uso! Usalo cliccando qui: http://t.me/{BOT_USERNAME} !")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', launch_web_ui))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('show_answers', mostra_dati_raccolti))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.run_polling()
    """
    Comandi per telegram:
    start - Scopri cosa può fare questo bot!
    help - Chiedi assistenza al bot
    show_answers - Visualizza i risultati
    https://aga19999.github.io/Telegram_bot4/prova.html
    """


