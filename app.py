from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, ContextTypes
from credentials import BOT_TOKEN, BOT_USERNAME, PASSWORD_DATABASE, MIO_ID_UTENTE
import pymysql.cursors
import json
import schedule
import time
from datetime import datetime

connection = pymysql.connect(host='localhost',
                             user='root',
                             password=PASSWORD_DATABASE,
                             database='telegramBot',
                             cursorclass=pymysql.cursors.DictCursor)

async def launch_web_ui(update: Update, callback: CallbackContext):
    kb = [
        [KeyboardButton("Clicca qui!", web_app=WebAppInfo('https://aga19999.github.io/Telegram_bot4/survey1.html'))]
    ]
    await update.message.reply_text("Iniziamo!", reply_markup=ReplyKeyboardMarkup(kb))

async def help(update: Update, callback: CallbackContext):
    await update.message.reply_text("Questo bot è rivolto al personale scolastico che intende interagire con" +
                                    "gli studenti tramite l'uso di sondaggi e altri widget")


async def web_app_data(update: Update, context: CallbackContext):
    data = json.loads(update.message.web_app_data.data)
    user_id = update.message.from_user.id
    # Trasforma data in una stringa per il database
    risposta_json = json.dumps(data)

    print(f"ID Utente dalla tabella utenti: {user_id}")
    print(f"Risposta da inserire nella tabella rilevazioni: {data}")

    try:

        # Inserisce l'utente
        with connection.cursor() as cursor:
            query_check_user = "SELECT * FROM utenti WHERE codice_utente = %s"
            cursor.execute(query_check_user, (str(user_id),))
            result = cursor.fetchone()

            if not result:
                query_insert_user = "INSERT INTO utenti (codice_utente) VALUES (%s)"
                cursor.execute(query_insert_user, (str(user_id),))
                connection.commit()

        # Ottiene l'id dell'utente dalla tabella utenti
        with connection.cursor() as cursor:
            # Prende l'id dalla tabella utenti e lo mette nella tabella rilevazioni
            codice_utente = "SELECT codice_utente FROM utenti WHERE codice_utente = %s"
            cursor.execute(codice_utente, (str(user_id)))
            user_result = cursor.fetchone()

            if user_result:
                user_id_from_table = user_result["codice_utente"]
                query = "INSERT INTO rilevazioni (id_utente, risposta, orarioInvio, orarioRisposta) VALUES (%s, %s, NULL, NULL)"
                cursor.execute(query, (user_id_from_table, risposta_json))
                connection.commit()

    except Exception as e:
        print(f"Errore durante l'elaborazione dei dati: {e}")

async def mostra_dati_raccolti(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    try:
        with connection.cursor() as cursor:
            # Ottiene l'ultima risposta dell'utente dalla tabella rilevazioni
            query = "SELECT risposta FROM rilevazioni WHERE id_utente = %s ORDER BY id DESC LIMIT 1"
            # La SELECT in basso serve per ottenere invece tutte le risposte dell'utente
            # SELECT risposta FROM rilevazioni WHERE id_utente = %s
            cursor.execute(query, (user_id))
            risposte = cursor.fetchall()

            # Elabora o stampa le risposte
            for response in risposte:
                await update.message.reply_text(f"Risposta: {response['risposta']}")

    except Exception as e:
        print(f"Errore durante il recupero delle risposte: {e}")

#


if __name__ == '__main__':
    print(f"Il bot è in uso! Usalo cliccando qui: http://t.me/{BOT_USERNAME} !")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', launch_web_ui))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('show_answers', mostra_dati_raccolti))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.run_polling()
    connection.close()
    """
    Comandi per telegram:
    start - Scopri cosa può fare questo bot!
    help - Chiedi assistenza al bot
    show_answers - Visualizza i risultati
    https://aga19999.github.io/Telegram_bot4/survey1.html
    https://aga19999.github.io/Telegram_bot4/survey2.html
    """


