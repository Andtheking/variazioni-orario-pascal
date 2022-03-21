TOKEN = '5264178692:AAG2aN936LktECE_GtEgmzONAq8Yvmpb4W4'


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
  host="sql4.freemysqlhosting.net",
  user="sql4480554",
  password="RSvsJVaa5q",
  database="sql4480554"
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
    update.message.reply_text("Imposta una classe con /impostaClasse: clicca il comando (o scrivilo) e poi manda la classe tipo 3A, 2F, 5I. Con /classe puoi vedere la classe impostata al momento. Ogni mattina alle 7.40 ti arriverà una notifica con le variazioni orario del giorno.")

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


    '''# Robo che potrebbe servirmi se database va male
    


    # file = open('utenti.txt', 'r+')
    # testoFile = file.read()
    # righe = testoFile.split('\n')
    # i = 0
    # for riga in righe:    
    #     dato = riga.split(',')
    #     i += 1
    # 
    #     
    #     if str(id) in dato[0]:
    #         esiste = True
    #         righe[i-1] = f"{dato[0]},{str(messaggio)}"
    #         break
    #         
    #     else:
    #         logger.info('Utente non trovato')
    #         esiste = False
    #        
    # if esiste == False:
    #     file.write(f"\n{str(id)},{str(messaggio)}".upper())
    #     file.close()
    #     logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha impostato \"{messaggio}\" come classe alle {update.message.date}")
    #     update.message.reply_text("Classe impostata.")
    # else:
    #     
    #     file.truncate(0)
    #     file.close()
    #     
    #     i = 0
    #     file = open('utenti.txt', 'w')
    #     for riga in righe:
    #         i += 1
    #         if i == len(righe):
    #             file.write(f"{str(riga)}")
    #         else:
    #             file.write(f"{str(riga)}\n")
    #     file.close()
    '''
    
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
    

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id=245996916&text=Bot%20online!')
     
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    
    imposta_classe = ConversationHandler(
        entry_points=[CommandHandler("impostaClasse", impostaClasse)],
        states={
            CLASSE: [MessageHandler(Filters.text & ~ Filters.command, ClasseImpostata)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dp.add_handler(CommandHandler('classe', classe))

    dp.add_handler(imposta_classe)
    
    dp.add_error_handler(error)
    

    schedule.every().day.at("00:05").do(GetUrl)

    schedule.every().monday.at("06:30").do(mandaMessaggio)
    schedule.every().tuesday.at("06:30").do(mandaMessaggio)
    schedule.every().wednesday.at("06:30").do(mandaMessaggio)
    schedule.every().thursday.at("06:30").do(mandaMessaggio)
    schedule.every().friday.at("06:30").do(mandaMessaggio)
    schedule.every().saturday.at("06:30").do(mandaMessaggio)
    

    

    Thread(target=schedule_checker).start()

    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN, webhook_url="https://variazioni-orario-pascal.herokuapp.com/" + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()