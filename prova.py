import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, Bot
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, ContextTypes, Updater
from credentials import BOT_TOKEN, BOT_USERNAME, PASSWORD_DATABASE, MIO_ID_UTENTE
import pymysql.cursors
import json
from datetime import datetime, timedelta

logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO

)

bot = Bot('BOT_TOKEN')

connection = pymysql.connect(host='localhost',
                             user='root',
                             password=PASSWORD_DATABASE,
                             database='telegramBot',
                             cursorclass=pymysql.cursors.DictCursor)

async def launch_web_ui(update: Update, callback: CallbackContext):
    await update.message.reply_text("Benvenuto/a!")

"""async def send_message_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=MIO_ID_UTENTE,text='job executed')"""

async def help(update: Update, callback: CallbackContext):
    await update.message.reply_text("Questo bot è rivolto al personale scolastico che intende interagire con" +
                                    "gli studenti tramite l'uso di sondaggi e altri widget")


async def web_app_data(update: Update, context: CallbackContext):
    data = json.loads(update.message.web_app_data.data)
    user_id = update.message.from_user.id

    # Trasformo data in una stringa per il database
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

            # Elabora o stampa le risposte a seconda delle tue esigenze
            for response in risposte:
                await update.message.reply_text(f"Risposta: {response['risposta']}")

    except Exception as e:
        print(f"Errore durante il recupero delle risposte: {e}")


async def invia_questionario(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    url = f"Clicca qui per completare il questionario: {data["survey"]}"
    print(url)
    # Manda il questionario all'utente
    print(f"Invio il questionario a {data["telegram_user_id"]} - Link: {url}")
    await context.bot.send_message(chat_id=data["telegram_user_id"], text=url)

async def fetch_elenco_sessioni(context: ContextTypes.DEFAULT_TYPE) -> None:
    with connection.cursor() as cursor:
        # Seleziona le sessioni nel prossimo minuto
        query = """SELECT dataInvio, u.telegram_user_id , us.id_utente, us.id_sessione, survey, stato 
                    FROM sessioni s 
                    INNER JOIN utenti_sessioni us 
                    ON s.id = us.id_sessione 
                    INNER JOIN utenti u ON u.id = us.id_utente 
                    WHERE dataInvio > %s AND dataInvio <= %s AND stato = 0"""
        now = datetime.now()
        half_before = now - timedelta(minutes=60)
        cursor.execute(query, (half_before, now))
        elenco_sessioni = cursor.fetchall()
        print(elenco_sessioni)
        for sessione in elenco_sessioni:
            context.job_queue.run_once(invia_questionario, now - timedelta(hours=1), data=sessione)
             # Aggiorna lo status della sessione evitando che venga ripetuta più volte
            with connection.cursor() as cursor:
                query_update_status = "UPDATE utenti_sessioni SET stato = 1 WHERE id_utente = %s AND id_sessione = %s"
                cursor.execute(query_update_status, (sessione["id_utente"], sessione["id_sessione"]))
                connection.commit()
                print(f"Stato della sessione aggiornato a 1 per l'utente {sessione["id_utente"]}")

async def aggiungi_sessioni_prova(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        with connection.cursor() as cursor:
            query = "INSERT INTO sessioni (dataInvio, id_utente, survey) VALUES (%s, %s, %s)"
            now = datetime.now()
            id_utente = MIO_ID_UTENTE
            messaggio = "Ehii"
            cursor.execute(query, (now, id_utente, messaggio))
            connection.commit()
            print("Query aggiunta con successo al database.")
    except Exception as e:
        print(f"Errore durante l'aggiunta della query al database: {e}")

if __name__ == '__main__':

    print(f"Il bot è in uso! Usalo cliccando qui: http://t.me/{BOT_USERNAME} !")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = application.job_queue
    job_queue.run_repeating(fetch_elenco_sessioni, interval=10.0, first=0.0)
    #job_queue.run_repeating(aggiungi_sessioni_prova, interval=60.0, first=0.0)
    #job_queue.run_repeating(controlla_invii, interval=10.0, first=0.0)
    application.add_handler(CommandHandler('start', launch_web_ui))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('show_answers', mostra_dati_raccolti))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    connection.close()


    """
        Comandi per telegram:
        start - Scopri cosa può fare questo bot!
        help - Chiedi assistenza al bot
        show_answers - Visualizza i risultati
        https://aga19999.github.io/Telegram_bot4/survey1.html
        https://aga19999.github.io/Telegram_bot4/survey2.html
    """
