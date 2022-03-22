TOKEN = '5264178692:AAG2aN936LktECE_GtEgmzONAq8Yvmpb4W4'


from warnings import catch_warnings
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

from sito import *
from threading import Thread
from time import sleep
from urllib.parse import urlparse
import mysql.connector

import os, requests, logging, schedule, redis


mydb = mysql.connector.connect(
  host="ilzyz0heng1bygi8.chr7pe7iynqr.eu-west-1.rds.amazonaws.com",
  user="koepuzylpoyuhzkq",
  password="zurn3w7ul0odctg2",
  database="wnci1nl0vgnh813j"
)


mycursor = mydb.cursor(buffered=True)


PORT = int(os.environ.get('PORT','8443'))

CLASSE = 0
ID_TELEGRAM_AND = "245996916"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

def help(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Imposta la tua classe con /impostaClasse: dopo averla impostata, la mattina alle 6.30 riceverai una notifica con le variazioni orario del giorno;\nVisualizza la tua classe con /classe;\nUsa /variazioni <CLASSE> per avere le variazioni orario di una qualsiasi classe.")

def start(update,context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Versione praticamente quasi finita. Fai /help.")

def impostaClasse(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Mandami la classe nel formato \"1A\" oppure annulla con /cancel")
    return CLASSE

def ClasseImpostata(update, context):
    
    id = update.message.from_user.id
    messaggio = str(update.message.text).upper()
    
    if len(messaggio) != 2:
        update.message.reply_text("Non hai inserito una classe")
        return
    try:
        if int(messaggio[0:1]) < 0 or int(messaggio[0:1]) > 5:
            update.message.reply_text("Non hai inserito una classe")
            return
    except Exception as ex:
        logging.warning(ex)
        update.message.reply_text("Non hai inserito una classe")
        return
    
    mycursor.execute(f'SELECT id, username, classe FROM utenti WHERE id={id};')
    idInTabella = mycursor.fetchall()

    if len(idInTabella) == 0:
        mycursor.execute(f'INSERT utenti (id, username, classe) VALUES (\"{id}\",\"{update.message.from_user.name}\",\"{messaggio}\");')
        logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha impostato \"{messaggio}\" come classe alle {update.message.date}")
        update.message.reply_text(f"Hai impostato \"{update.message.text}\" come classe. Riceverai una notifica alle 7.40 ogni mattina con le variazioni orario. Per disiscriverti blocca il bot. (Farò un comando prima o poi)")
    else:
        mycursor.execute(f'UPDATE utenti SET classe=\"{messaggio}\" WHERE id=\"{id}\";')
        logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha cambiato classe da {idInTabella[0][2]} a {str(messaggio)}. Data e ora: {update.message.date}")
        update.message.reply_text(f"Avevi già una classe impostata ({idInTabella[0][2]}), l'ho cambiata in {str(messaggio)}.")
    
    mydb.commit()

    return ConversationHandler.END

def classe(update, context):
    id = update.message.from_user.id
    messaggio = update.message.text

    mycursor.execute(f'SELECT id, username, classe FROM utenti WHERE id={id};')
    idInTabella = mycursor.fetchall()

    if len(idInTabella) == 0:
        logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha una classe. Data e ora: {update.message.date}")
        update.message.reply_text(f"Non hai una classe impostata. Impostala con /impostaClasse")

    else:
        logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha visto la sua classe alle {update.message.date}")
        update.message.reply_text(f"Classe attuale: {idInTabella[0][2]}")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def cancel(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha cancellato l'impostazione della classe alle {update.message.date}")
    update.message.reply_text("Azione annullata.")
    return ConversationHandler.END

def mandaMessaggio():
    mycursor.execute(f'SELECT id, username, classe FROM utenti')
    
    idInTabella = mycursor.fetchall()
    
    if len(idInTabella) != 0:    
        for utente in idInTabella:
            id = utente[0]
            requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={id}&text={Main(utente[2])}')
    
def variazioni(update, context):
    messaggio = str(update.message.text).replace('/variazioni ', '')
    try:
        if (int(messaggio[0:1]) > 0 and int(messaggio[0:1]) < 6) and len(messaggio) == 2: 
            requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={ID_TELEGRAM_AND}&text={Main(messaggio)}')
        else:
            update.message.reply_text('Non hai inserito una classe valida. Il formato è: /variazioni 3A')
    except:
        update.message.reply_text('Non hai inserito una classe valida. Il formato è: /variazioni 3A')

def discord(update, context):
    update.message.reply_text('Il discord del Pascal: https://discord.gg/UmUu6ZNMJy')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id=245996916&text=Bot%20online!')
     
    
    imposta_classe = ConversationHandler(
        entry_points=[CommandHandler("impostaClasse", impostaClasse)],
        states={
            CLASSE: [MessageHandler(Filters.text & ~ Filters.command, ClasseImpostata)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dp.add_handler(CommandHandler("start", start)) 
    dp.add_handler(CommandHandler("help", help)) # Aiuto su come si usa il bot

    dp.add_handler(CommandHandler('classe', classe)) # Visualizza la classe che hai scelto per le notifiche la mattina

    dp.add_handler(CommandHandler('variazioni', variazioni)) # Visualizza variazioni di un'altra classe del giorno

    dp.add_handler(CommandHandler('discord', discord)) # Discord del pascal

    dp.add_handler(imposta_classe) # Comando per impostare la classe per le notifiche
    
    dp.add_error_handler(error) # In caso di errore:
    

    #schedule.every().day.at("00:05").do(GetUrl)

    schedule.every().monday.at("06:30").do(mandaMessaggio)
    schedule.every().tuesday.at("06:30").do(mandaMessaggio)
    schedule.every().wednesday.at("06:30").do(mandaMessaggio)
    schedule.every().thursday.at("06:30").do(mandaMessaggio)
    schedule.every().friday.at("06:30").do(mandaMessaggio)
    schedule.every().saturday.at("06:30").do(mandaMessaggio)
    
    
    

    Thread(target=schedule_checker).start()

    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN, webhook_url="https://variazioni-orario-pascal.herokuapp.com/" + TOKEN)
    #updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()