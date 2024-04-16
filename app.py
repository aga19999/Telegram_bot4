from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo, Bot
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, ContextTypes
from credentials import BOT_TOKEN, BOT_USERNAME, PASSWORD_DATABASE
import pymysql.cursors
import json
from datetime import datetime, timedelta
import logging

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


async def help(update: Update, callback: CallbackContext):
    await update.message.reply_text("""Questo bot è rivolto ai pazienti e permette di metterli in comunicazione"
                                    con il loro terapeuta attraverso la compilazione di questionari""")

    # Questo bot è rivolto al personale scolastico che intende interagire con
    # gli studenti tramite l'uso di sondaggi e altri widget


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
            query_check_user = "SELECT * FROM utenti WHERE telegram_user_id = %s"
            cursor.execute(query_check_user, (str(user_id)))
            result = cursor.fetchone()

            if not result:
                query_insert_user = "INSERT INTO utenti (telegram_user_id) VALUES (%s)"
                cursor.execute(query_insert_user, (str(user_id)))
                connection.commit()

        # Ottiene l'id dell'utente dalla tabella utenti
        with connection.cursor() as cursor:
            # Prende l'id dalla tabella utenti e lo mette nella tabella rilevazioni
            codice_utente = "SELECT telegram_user_id FROM utenti WHERE telegram_user_id = %s"
            cursor.execute(codice_utente, (str(user_id)))
            user_result = cursor.fetchone()

            if user_result:
                # Ottiene l'id della sessione associata all'utente dalla tabella utenti_sessioni
                query_session_id = """SELECT us.id_sessione 
                                      FROM utenti_sessioni us
                                      JOIN utenti u
                                      ON us.id_utente = u.id
                                      WHERE u.telegram_user_id = %s"""
                cursor.execute(query_session_id, (user_result["telegram_user_id"]))
                session_id_result = cursor.fetchone()
                if session_id_result:
                    sessione_id = session_id_result["id_sessione"]
                    now = datetime.now()
                    # Inserisce l'id dell'utente, l'id della sessione e la risposta nella tabella rilevazioni
                    query_insert_response = ("""INSERT INTO rilevazioni (id_utente, id_sessione, risposta, orarioRisposta)
                                                VALUES (%s, %s, %s, %s)""")
                    cursor.execute(query_insert_response, (user_result["telegram_user_id"],
                                                           sessione_id, risposta_json, now))
                    connection.commit()
                    # Manda una risposta all'utente dopo aver salvato i dati ricevuti
                    await context.bot.send_message(chat_id=user_result["telegram_user_id"],
                                                   text="Grazie per aver compilato il sondaggio!",
                                                   reply_markup=ReplyKeyboardRemove())

    except Exception as e:
        print(f"Errore durante l'elaborazione dei dati: {e}")


async def mostra_dati_raccolti(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    try:
        with connection.cursor() as cursor:
            # Ottiene l'ultima risposta dell'utente dalla tabella rilevazioni
            query = "SELECT risposta FROM rilevazioni WHERE id_utente = %s ORDER BY id DESC LIMIT 1"
            cursor.execute(query, user_id)
            risposte = cursor.fetchall()
            # Manda i risultati all'utente
            for risposta in risposte:
                await update.message.reply_text(f"Risposta: {risposta['risposta']}")

    except Exception as e:
        print(f"Errore durante il recupero delle risposte: {e}")


async def invia_questionario(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    now = datetime.now() - timedelta(hours=2)
    # Posso inserire direttamente la chiave tra apici senza indicare la posizione
    # grazie alla libreria SQLAlchemy
    url = data["survey"]
    id_utente = data["telegram_user_id"]
    context.job_queue.run_once(reminder_utente, now + timedelta(seconds=20), data=data)
    # Manda il questionario all'utente
    kb = [
        [KeyboardButton("Clicca qui!", web_app=WebAppInfo(url))]
    ]
    await context.bot.send_message(chat_id=id_utente,
                                   text="Ciao! Clicca in basso per compilare il sondaggio",
                                   reply_markup=ReplyKeyboardMarkup(kb))
    print(f"Invio il questionario a {data["telegram_user_id"]} - Link: {url}")


async def reminder_utente(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = context.job.data
        url = data["survey"]
        id_utente = data["telegram_user_id"]
        id_sessione = data["id_sessione"]
        now = datetime.now() - timedelta(hours=2)

        with connection.cursor() as cursor:
            # Per evitare delle eccezioni seleziona il numero di righe a cui è associata l'id della sessione
            # Se il valore è 0 allora l'utente non ha compilato il questionario
            # Se il valore è 1 allora l'utente ha già compilato il questionario e non verrà mandato il reminder
            query = """SELECT *
                        FROM rilevazioni 
                        WHERE id_sessione = %s AND id_utente = %s"""
            cursor.execute(query, (id_sessione, id_utente))
            rilevazione = cursor.fetchone()


            # Se il conteggio è zero, invia il reminder
            if rilevazione is None:
                # Richiamo la funzione di timeout nel caso in cui anche dopo il reminder l'utente decida di non
                # compilare il questionario
                # context.job_queue.run_once(timeout_sondaggio, now + timedelta(seconds=20), data=data)
                kb = [
                    [KeyboardButton("Clicca qui!", web_app=WebAppInfo(url))]
                ]
                await context.bot.send_message(chat_id=id_utente,
                                               text="Ehi, ti sei dimenticato di compilare il questionario! Clicca qui sotto!",
                                               reply_markup=ReplyKeyboardMarkup(kb))
    except Exception as e:
        logging.error(
            f"Si è verificato un errore: {type(e).__name__} - {e}")


""" Se l'utente dopo il reminder non compila il questionario,
                    esaurisce la possibilità di farlo """
async def timeout_sondaggio(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = context.job.data
        id_utente = data["telegram_user_id"]
        id_sessione = data["id_sessione"]

        with connection.cursor() as cursor:
            # Per evitare delle eccezioni seleziona il numero di righe a cui è associata l'id della sessione
            # Se il valore è 0 allora l'utente non ha compilato il questionario
            # Se il valore è 1 allora l'utente ha già compilato il questionario e non verrà mandato il reminder
            query = """SELECT COUNT(*)
                                   FROM rilevazioni 
                                   WHERE id_sessione = %s"""
            cursor.execute(query, (id_sessione,))
            count = cursor.fetchone()  # Ottieni il valore del conteggio
            # Se il conteggio è zero, invia il reminder
            if count['COUNT(*)'] == 0:
                await context.bot.send_message(chat_id=id_utente,
                                               text="Ops! Tempo scaduto. Sondaggio non più disponibile",
                                               reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logging.error(
            f"Si è verificato un errore: {type(e).__name__} - {e}")

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
        one_hours_after = now + timedelta(minutes=60)
        cursor.execute(query, (now, one_hours_after))
        elenco_sessioni = cursor.fetchall()
        for elenco in elenco_sessioni:
            if elenco_sessioni is not None:
                print(elenco)

        for sessione in elenco_sessioni:
            context.job_queue.run_once(invia_questionario, (sessione["dataInvio"] - timedelta(hours=2)), data=sessione)
            # Aggiorna lo status della sessione evitando che venga ripetuta più volte
            with connection.cursor() as cursor1:
                query_update_status = "UPDATE utenti_sessioni SET stato = 1 WHERE id_utente = %s AND id_sessione = %s"
                cursor1.execute(query_update_status, (sessione["id_utente"], sessione["id_sessione"]))
                connection.commit()


if __name__ == '__main__':
    print(f"Il bot è in uso! Usalo cliccando qui: http://t.me/{BOT_USERNAME} !")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = application.job_queue
    job_queue.run_repeating(fetch_elenco_sessioni, interval=10.0, first=0.0)
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

