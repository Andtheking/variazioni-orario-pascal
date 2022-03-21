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
import os, requests, logging, schedule
from threading import Thread
from time import sleep

PORT = int(os.environ.get('PORT','8443'))

CLASSE = 0


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

def help(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Imposta una classe con /impostaClasse: clicca il comando (o scrivilo) e poi manda la classe tipo 3A, 2F, 5I. Con /classe puoi vedere la classe impostata al momento.")

def start(update,context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Seconda versione del bot (fa ancora un po\' cagare): clicca /impostaClasse")

def impostaClasse(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Mandami la classe nel formato \"1A\" oppure annulla con /cancel")
    return CLASSE

def ClasseImpostata(update, context):
    
    id = update.message.from_user.id
    
    if len(update.message.text) != 2:
        update.message.reply_text("Non hai inserito una classe")
        return
    try:
        if int(update.message.text[0:1]) < 0 and int(update.message.text[0:1]) > 5:
            update.message.reply_text("Non hai inserito una classe")
            return
    except Exception as ex:
        logging.warning(ex)
        update.message.reply_text("Non hai inserito una classe")
        return


    file = open('utenti.txt', 'r+')
    testoFile = file.read()
    righe = testoFile.split('\n')
    i = 0
    for riga in righe:    
        dato = riga.split(',')
        i += 1

        
        if str(id) in dato[0]:
            esiste = True
            righe[i-1] = f"{dato[0]},{str(update.message.text)}"
            break
            
        else:
            logger.info('Utente non trovato')
            esiste = False
           
    if esiste == False:
        file.write(f"\n{str(id)},{str(update.message.text)}".upper())
        file.close()
        logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha impostato \"{update.message.text}\" come classe alle {update.message.date}")
        update.message.reply_text("Classe impostata.")
    else:
        
        file.truncate(0)
        file.close()
        
        i = 0
        file = open('utenti.txt', 'w')
        for riga in righe:
            i += 1
            if i == len(righe):
                file.write(f"{str(riga)}")
            else:
                file.write(f"{str(riga)}\n")
        file.close()
        
        logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha cambiato classe da {dato[1]} a {str(update.message.text)}. Data e ora: {update.message.date}")
        update.message.reply_text(f"Avevi già una classe impostata ({dato[1]}), l'ho cambiata in {str(update.message.text)}.")

    return ConversationHandler.END

def classe(update, context):
    id = update.message.from_user.id
    
    file = open('utenti.txt', 'r+')
    testoFile = file.read()
    righe = testoFile.split('\n')\
    
    for riga in righe:    
        dato = riga.split(',')

        if str(id) in dato[0]:
            logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha visto la sua classe alle {update.message.date}")
            update.message.reply_text(f"Classe attuale: {dato[1]}")
            classe = True
            break
        else:
            classe = False
    
    if classe == False:
        logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha una classe. Data e ora: {update.message.date}")
        update.message.reply_text(f"Non hai una classe impostata. Impostala con /impostaClasse")

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def cancel(update, context):
    logger.info(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha cancellato l'impostazione della classe alle {update.message.date}")
    update.message.reply_text("Azione annullata.")
    return ConversationHandler.END

def mandaMessaggio():
    file = open('utenti.txt', 'r+')
    testoFile = file.read()
    righe = testoFile.split('\n')
    i = 0
    
    for riga in righe:    
        dato = riga.split(',')
        id = dato[0]
        requests.post(f'https://api.telegram.org/bot5264178692:AAG2aN936LktECE_GtEgmzONAq8Yvmpb4W4/sendMessage?chat_id={id}&text=Funziona, ora devo fare la parte importante ma fin quando la farò sto messaggio arriverà ogni giorno alle 7.40')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    requests.post('https://api.telegram.org/bot5264178692:AAG2aN936LktECE_GtEgmzONAq8Yvmpb4W4/sendMessage?chat_id=245996916&text=Bot%20online!')
     
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
    
    schedule.every().monday.at("07:40").do(mandaMessaggio)
    schedule.every().tuesday.at("07:40").do(mandaMessaggio)
    schedule.every().wednesday.at("07:40").do(mandaMessaggio)
    schedule.every().thursday.at("07:40").do(mandaMessaggio)
    schedule.every().friday.at("07:40").do(mandaMessaggio)
    schedule.every().saturday.at("07:40").do(mandaMessaggio)

    Thread(target=schedule_checker).start()

    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN, webhook_url="https://variazioni-orario-pascal.herokuapp.com/" + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()