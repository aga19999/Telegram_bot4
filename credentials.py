"""credentials.py"""
import os
if os.path.exists(".env"):
    # se trovi il file env caricalo
    from dotenv import load_dotenv
    load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')
PASSWORD_DATABASE = os.getenv('PASSWORD_DATABASE')
MIO_ID_UTENTE = os.getenv('MIO_ID_UTENTE')