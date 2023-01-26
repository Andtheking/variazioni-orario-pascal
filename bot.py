TOKEN = None

MANDO = True

ID_CANALE_LOG = '-1001741378490'

with open("Roba sensibile/token.txt","r") as file:
    TOKEN = file.read().splitlines()[0]

import logging
import os
import re
from threading import Thread
from time import sleep
from bs4 import BeautifulSoup

import mysql.connector
import requests
import schedule
from telegram import Bot, Message, Update, User
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)


import python_scripts.variazioni.variazioniLive as variazioniLive
from python_scripts.variazioni.variazioni import CancellaCartellaPdf, Main, controllaVariazioniAule


# 0 = Host
# 1 = User
# 2 = Password
# 3 = Database

with open("Roba sensibile/database.txt","r") as file:
    credenziali_database = file.read().splitlines()

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

mydb = None
mycursor = None

days = "|oggi|domani"


#https://regex101.com/r/5s6yUW/1
rVar = re.compile(r"(/variazioni) ?([1-5](?:[a-z]|[A-Z]))? ?(\b(?:(?:0[1-9]|[1-9])|[12][0-9]|3[01])\b(?:-|\/)\b(?:(0[1-9]|[1-9])|1[0-2])\b"+days+")?$")


rImp = re.compile(r"^[1-5](?:[a-z]|[A-Z])$")

def database_connection():
	global mydb
	global mycursor

	mydb = mysql.connector.connect(
	  host=credenziali_database[0],
	  user=credenziali_database[1],
	  password=credenziali_database[2],
	  database=credenziali_database[3]
	)

	mycursor = mydb.cursor(buffered=True)

def database_disconnection():
	global mydb
	global mycursor

	mydb.disconnect() if mydb != None else print("No database")
	mydb = None
	mycursor = None

def log(messaggio: str):
    logger.info(messaggio)
    with open('log.txt','a') as f:
        f.write(messaggio + "\n")


def help(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    
    update.message.reply_text("""Imposta la tua classe con /impostaClasse;
Dopo averla impostata, la sera alle 21:00 e la mattina alle 6.30 riceverai una notifica con le variazioni orario del giorno dopo e attuale;
Visualizza la tua classe con /classe;
Usa /variazioni <CLASSE> <DD-MM> per avere le variazioni orario di una qualsiasi classe di un qualsiasi giorno.""") 

def start(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Versione 2.0 \"in dubbio\". Potrebbe non funzionare bene.\nFai /help.")

def impostaClasse(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Mandami la classe nel formato \"1A\" oppure annulla con /cancel")
    return CLASSE

def broadcast(update: Update, contex: CallbackContext):
    global mycursor
    
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    if (update.message.from_user['id'] == int(ID_TELEGRAM_AND)):
        log("Ed ha il permesso")

        database_connection()
        mycursor.execute(f'SELECT id, username, classe FROM utenti')
        idInTabella = mycursor.fetchall()
        database_disconnection()
    
        contex.bot.send_message(ID_CANALE_LOG,f'Inizio a mandare il messaggio agli utenti:\n\n"{update.message.text.replace("/broadcast ", "")}"')
        log(f'Inizio a mandare il messaggio agli utenti:\n\n"{update.message.text.replace("/broadcast ", "")}"')


        if len(idInTabella) != 0:    
            for utente in idInTabella:
                id = utente[0]
                tuttoOk = False
                while tuttoOk:
                    try:
                        contex.bot.send_message(id,update.message.text.replace("/broadcast ",""))
                        log(f"Messaggio inviato a {utente[1]}, {utente[0]}")
                        tuttoOk = True
                    except:
                        tuttoOk = False
        
        contex.bot.send_message(ID_CANALE_LOG,'Ho finito di mandare il messaggio agli utenti')
        log('Ho finito di mandare il messaggio agli utenti')


    else:
        update.message.reply_text("Non hai il permesso.")
        log("E non ha il permesso")



def ClasseImpostata(update: Update, context: CallbackContext):
    global mycursor
    global mydb
    global rImp

    id = update.message.from_user.id
    roboAntiCrashPerEdit = update.message if update.message is not None else update.edited_message
    messaggio = str(roboAntiCrashPerEdit.text).upper()
    
    m = rImp.match(messaggio)

    if not m:
        roboAntiCrashPerEdit.reply_text("Non hai inserito una classe valida (1-5A-Z o 1-5a-z)")
        return
    
    database_connection()
    mycursor.execute(f'SELECT id, username, classe FROM utenti WHERE id={id};')
    idInTabella = mycursor.fetchall()

    if len(idInTabella) == 0:
        mycursor.execute(f'INSERT utenti (id, username, classe) VALUES (\"{id}\",\"{roboAntiCrashPerEdit.from_user.name}\",\"{messaggio}\");')
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha impostato \"{messaggio}\" come classe alle {roboAntiCrashPerEdit.date}")
        roboAntiCrashPerEdit.reply_text(f"Hai impostato \"{roboAntiCrashPerEdit.text}\" come classe. Riceverai una notifica alle 6.30 ogni mattina e alle 21:00 ogni sera con le variazioni orario. Per non ricevere più notifiche e annunci: /off")
    else:
        mycursor.execute(f'UPDATE utenti SET classe=\"{messaggio}\" WHERE id=\"{id}\";')
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha cambiato classe da {idInTabella[0][2]} a {str(messaggio)}. Data e ora: {roboAntiCrashPerEdit.date}")
        roboAntiCrashPerEdit.reply_text(f"Avevi già una classe impostata ({idInTabella[0][2]}), l'ho cambiata in {str(messaggio)}.")
    
    mydb.commit()
    database_disconnection()
    return ConversationHandler.END

def classe(update: Update, context: CallbackContext):
    global mycursor
    id = update.message.from_user.id
    messaggio = update.message.text


    database_connection()
    mycursor.execute(f'SELECT id, username, classe FROM utenti WHERE id={id};')
    idInTabella = mycursor.fetchall()
    database_disconnection()

    if len(idInTabella) == 0:
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha una classe. ({messaggio}) Data e ora: {update.message.date}")
        update.message.reply_text(f"Non hai una classe impostata. Impostala con /impostaClasse")

    else:
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha visto la sua classe alle {update.message.date}")
        update.message.reply_text(f"Classe attuale: {idInTabella[0][2]}")


def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    context.bot.send_message(ID_CANALE_LOG, text=f'{context.bot.name}\nUpdate "{update}" caused error "{context.error}')
    log(f'Update "{update}" caused error "{context.error}')

def cancel(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha cancellato l'impostazione della classe alle {update.message.date}")
    update.message.reply_text("Azione annullata.")
    return ConversationHandler.END


def mandaMessaggio(giornoPrima: bool, bot: Bot):
    if MANDO:
        global mycursor

        database_connection()
        log(f"Inizio a mandare le variazioni agli utenti")
        mycursor.execute(f'SELECT id, username, classe FROM utenti')
    
        idInTabella = mycursor.fetchall()
        database_disconnection()

        if len(idInTabella) != 0:    
            for utente in idInTabella:
                id = utente[0]
                MandaVariazioni(bot=bot, classe=utente[2], giorno="domani" if giornoPrima else "oggi",chatId=id)
                log(f"Variazioni di {'domani' if giornoPrima else 'oggi'} mandate a: {utente[1]}")



def getLink(update: Update, context: CallbackContext):

    robaAntiCrashPerEdit = update.message if update.message != None else update.edited_message
    
    log(f"{update.message.from_user.name}, {update.message.from_user.id} ha fatto {robaAntiCrashPerEdit.text}")

    dati = robaAntiCrashPerEdit.text.lower().replace('/linkpdf ', '')

    datiList = dati.strip().split(" ")
    robaAntiCrashPerEdit.reply_text(Main(datiList[0].upper().strip(),giorno = datiList[1].strip() if len(datiList) > 1 else "",onlyLink=True))


ALIAS_GIORNI = ["","domani","oggi"]

import time

def variazioni(update: Update, context: CallbackContext):
    global mycursor
    global rVar
    
    robaAntiCrashPerEdit = update.message if update.message != None else update.edited_message
    messaggioNonValido = 'Messaggio non valido. Il formato è: /variazioni 3A [GIORNO-MESE] (giorno e mese a numero, domani se omessi)'
    
    id = robaAntiCrashPerEdit.from_user['id']

    log(f"{robaAntiCrashPerEdit.from_user['name']}, {robaAntiCrashPerEdit.from_user['id']} ha eseguito \"{robaAntiCrashPerEdit.text}\" alle {robaAntiCrashPerEdit.date}")
    
    m = rVar.match(robaAntiCrashPerEdit.text) # deve matchare questo: https://regex101.com/r/fCC5e3/1

    if not m:
        robaAntiCrashPerEdit.reply_text(messaggioNonValido)
        return

    classe = m.group(2)
    giorno = m.group(3)

    if (classe is None):
        database_connection()
        mycursor.execute(f'SELECT id, username, classe FROM utenti WHERE id={id};')
        idInTabella = mycursor.fetchall()
        classe: str = idInTabella[0][2] if len(idInTabella) > 0 else None
        database_disconnection()
    
    if classe is None:
        robaAntiCrashPerEdit.reply_text("Non hai una classe impostata con /impostaclasse, devi specificarla con `/variazioni CLASSE GIORNO-MESE`",parse_mode='Markdown')
        return
    
    giorno = "domani" if giorno is None else giorno
    
    id = robaAntiCrashPerEdit.from_user.id
    
    MandaVariazioni(context.bot, classe.upper(), giorno, id)


def MandaVariazioni(bot: Bot, classe: str, giorno: str, chatId: int):
    try:
        variazioniOrario = f"{Main(classe,giorno)}"
        variazioniAule = f"{controllaVariazioniAule(classe,giorno)}"

        tuttoOk = False
        while tuttoOk:
            try:
                bot.send_message(chat_id=chatId, text=variazioniOrario, parse_mode='Markdown')
                if variazioniAule != '':
                    bot.send_message(chat_id=chatId, text=variazioniAule, parse_mode='Markdown')
                tuttoOk = True
            except:
                tuttoOk = False
    except Exception as e:
        # robaAntiCrashPerEdit.reply_text('Messaggio non valido. Il formato è: /variazioni 3A GIORNO-MESE (giorno e mese a numero)')
        try: # Se l'utente ha bloccato il bot esplode tutto
            bot.send_message(chat_id=chatId,text="Qualcosa è andato storto, whoops. Nel dubbio riprova")
            bot.send_message(chat_id = ID_CANALE_LOG, text=f'{str(e)}')
            log(f'{str(e)}')
        except:
            pass

def discord(update: Update, context: CallbackContext):
    update.message.reply_text('Discord del Pascal: https://discord.gg/UmUu6ZNMJy')

def off(update: Update, context: CallbackContext):
    id = update.message.from_user.id

    global mycursor
    global mydb

    database_connection()
    mycursor.execute(f'SELECT id, username, classe FROM utenti WHERE id={id};')
    idInTabella = mycursor.fetchall()

    if len(idInTabella) == 0:
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha una classe. ({update.message.text}) Data e ora: {update.message.date}")
        update.message.reply_text(f"Non hai una classe impostata. Se hai provato a disattivare le notifiche non credo tu voglia impostare una classe, ma nel dubbio si fa con /impostaClasse")

    else:
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha rimosso il suo id dal database dell'inoltro alle {update.message.date}")
        mycursor.execute(f'DELETE FROM utenti WHERE id=\"{id}\";')
        update.message.reply_text('Non riceverai più notifiche. Per riabilitare le notifiche devi rifare /impostaClasse.')
        mydb.commit()
    database_disconnection()


def backupUtenti():
    utenti = ottieni_utenti()
    
    with open('Roba sensibile/backupUtenti.txt','a') as f:
        f.write("--------------------------------------\n")
        for utente in utenti:
            f.write(f"{utente[0]} - {utente[1]} - {utente[2]}\n")

def canale(update: Update, context: CallbackContext):
    update.message.reply_text('Canale del bot: https://t.me/+7EexVd-RIoIwZjc0')


def spegniNotifiche(update: Update, context: CallbackContext):
    
    if (str(update.message.from_user.id) != ID_TELEGRAM_AND):
        update.message.reply_text("Non hai il permesso!")
        log (f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha il permesso per \"{update.message.text}\" alle {update.message.date}")
        return
    
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    
    global MANDO
    MANDO = False
    
    update.message.reply_text("Notifiche spente per tutti gli utenti")

def accendiNotifiche(update: Update, context: CallbackContext):
    if (str(update.message.from_user.id) != ID_TELEGRAM_AND):
        log (f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha il permesso per \"{update.message.text}\" alle {update.message.date}")
        update.message.reply_text("Non hai il permesso!")
        return

    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")

    global MANDO
    MANDO = True
    update.message.reply_text("Notifiche accese per tutti gli utenti")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    
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

    dp.add_handler(CommandHandler('variazioni', variazioni, run_async=True)) # Visualizza variazioni di un'altra classe del giorno

    dp.add_handler(CommandHandler('discord', discord)) # Discord del pascal

    dp.add_handler(CommandHandler('broadcast', broadcast))
    dp.add_handler(CommandHandler('linkPdf', getLink))
    dp.add_handler(CommandHandler('canale', canale))

    dp.add_handler(CommandHandler('accendiNotifiche', accendiNotifiche))
    dp.add_handler(CommandHandler('spegniNotifiche', spegniNotifiche))

    dp.add_handler(imposta_classe) # Comando per impostare la classe per le notifiche
    
    dp.add_error_handler(error) # In caso di errore:
    
    dp.add_handler(CommandHandler('off',off))
    
    ORARIO_MATTINA = "06:30"
    schedule.every().monday.at(ORARIO_MATTINA).do(mandaMessaggio,False,dp.bot)
    schedule.every().tuesday.at(ORARIO_MATTINA).do(mandaMessaggio,False,dp.bot)
    schedule.every().wednesday.at(ORARIO_MATTINA).do(mandaMessaggio,False,dp.bot)
    schedule.every().thursday.at(ORARIO_MATTINA).do(mandaMessaggio,False,dp.bot)
    schedule.every().friday.at(ORARIO_MATTINA).do(mandaMessaggio,False,dp.bot)
    schedule.every().saturday.at(ORARIO_MATTINA).do(mandaMessaggio,False,dp.bot)
    
    ORARIO_SERA = "21:00"
    schedule.every().monday.at(ORARIO_SERA).do(mandaMessaggio,True,dp.bot)
    schedule.every().tuesday.at(ORARIO_SERA).do(mandaMessaggio,True,dp.bot)
    schedule.every().wednesday.at(ORARIO_SERA).do(mandaMessaggio,True,dp.bot)
    schedule.every().thursday.at(ORARIO_SERA).do(mandaMessaggio,True,dp.bot)
    schedule.every().friday.at(ORARIO_SERA).do(mandaMessaggio,True,dp.bot)
    # Niente sabato perché darebbe per domenica
    schedule.every().sunday.at(ORARIO_SERA).do(mandaMessaggio,True,dp.bot)

    schedule.every().day.at("00:00").do(CancellaCartellaPdf)
    schedule.every().day.at("00:00").do(backupUtenti)

    Thread(target=schedule_checker).start()


    Thread(target=check, args=[dp.bot]).start()


    # updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN, webhook_url="https://variazioni-orario-pascal.herokuapp.com/" + TOKEN)
    updater.start_polling(timeout=200)
    updater.idle()



URL = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"
lastcheck = [""]

def check(bot):
    global lastcheck

    utenti = ottieni_utenti()

    while True:
        # download the homepage
        Ok = False
        while not Ok:
            try:
                response = requests.get(URL)
                soup = BeautifulSoup(response.text, 'html.parser')
                Ok = True
            except:
                Ok = False
        
        mod = soup.find_all(property="article:modified_time")
        if lastcheck[0] == mod[0]:
            print("Aspetto")
            time.sleep(300) # 5 min
            continue
        else:
            lastcheck = mod
            variazioniLive.ottieni_info(utenti=utenti, bot=bot, soup=soup)

def ottieni_utenti():
    database_connection()
    mycursor.execute(f'SELECT * FROM utenti;')
    utenti: list[list[str]] = mycursor.fetchall()
    database_disconnection()
    
    return utenti

if __name__ == '__main__':
    main()