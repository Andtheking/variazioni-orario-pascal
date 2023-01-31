TOKEN = None
MANDO = True

ID_CANALE_LOG = '-1001837249321'

with open("Roba sensibile/token.txt","r") as file:
    TOKEN = file.read().splitlines()[0]

import hashlib
import logging
import re
from threading import Thread
from time import sleep
from bs4 import BeautifulSoup

import mysql.connector
import requests
import schedule

from telegram import Bot, Message, Update, User
from telegram.error import Unauthorized
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)


import python_scripts.variazioni.variazioniLive as variazioniLive
import python_scripts.variazioni.variazioni as variazioniFile


# 0 = Host
# 1 = User
# 2 = Password
# 3 = Database

with open("Roba sensibile/database.txt","r") as file:
    credenziali_database = file.read().splitlines()

# PORT = int(os.environ.get('PORT','8443'))

CLASSE = 0
ID_TELEGRAM_AND = "245996916"

ADMINS: dict[int,str] = {
    245996916:"A", # @Andtheking, me stesso
    503421671:"E", # @NiniEdo, Edoardo Nini 5L mi ha aiutato un po' con la versione 3.0 e hosta lui il bot.
}

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

	mydb.disconnect() if mydb != None else log("No database")
	mydb = None
	mycursor = None

def log(messaggio: str, bot: Bot = None):
    logger.info(messaggio)
    with open('log.txt','a') as f:
        f.write(time.asctime() + " - " + messaggio + "\n")

    if bot == None:
        return

    bot.send_message(chat_id=ID_CANALE_LOG,text=messaggio)
    
        
def help(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    
    update.message.reply_text("""Imposta la tua classe con /impostaClasse;
Dopo averla impostata, la sera alle 21:00 e la mattina alle 6.30 riceverai una notifica con le variazioni orario del giorno dopo e attuale;
Visualizza la tua classe con /classe;
Usa /variazioni <CLASSE> <DD-MM> per avere le variazioni orario di una qualsiasi classe di un qualsiasi giorno.""") 

def start(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Versione 3.0 in prova. Potrebbe non funzionare bene.\nFai /help.")

def impostaClasse(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Mandami la classe nel formato \"1A\" oppure annulla con /cancel")
    return CLASSE

def broadcast(update: Update, contex: CallbackContext):
    global mycursor
    
    log(
        f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}",
        contex.bot
        )

    if (update.message.from_user['id'] in ADMINS):
        log("Ed ha il permesso",contex.bot)

        messaggio = update.message.text.replace("/broadcast","").strip()

        if len(messaggio) == 0:
            update.message.reply_text("Nessun messaggio, l'hai cliccato? lol")
            log("Ma non ha scritto nulla",contex.bot)
            return

        log(f'Inizio a mandare il messaggio agli utenti:\n\n"{update.message.text.replace("/broadcast ", "")}"',contex.bot)

        for utente in ottieni_utenti():
            id = utente[0]
            mandaSeNonBloccato(
                bot=contex.bot,
                chat_id=id,
                text=update.message.text.replace("/broadcast ","") + f"\n\n~{ADMINS[update.message.from_user['id']]}"
                )
            log(f"Messaggio inviato a {utente[1]}, {utente[0]}")
        
        log('Ho finito di mandare il messaggio agli utenti',contex.bot)
    else:
        update.message.reply_text("Non hai il permesso!")
        log("Ma non ha il permesso",contex.bot)

# TODO: Finire di cambiare le chiamate del metodo log() quando posso mettere context.bot

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
    
# TODO: CONTINUARE DA QUI
    utenti = ottieniUtentiDaID(id=id)
    
    database_connection()
    if len(utenti) == 0:
        mycursor.execute(f'INSERT utenti (id, username, classe) VALUES (\"{id}\",\"{roboAntiCrashPerEdit.from_user.name}\",\"{messaggio}\");')
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha impostato \"{messaggio}\" come classe alle {roboAntiCrashPerEdit.date}")
        roboAntiCrashPerEdit.reply_text(f"Hai impostato \"{roboAntiCrashPerEdit.text}\" come classe. Riceverai una notifica alle 6.30 ogni mattina e alle 21:00 ogni sera con le variazioni orario. Per non ricevere più notifiche e annunci: /off")
    else:
        mycursor.execute(f'UPDATE utenti SET classe=\"{messaggio}\" WHERE id=\"{id}\";')
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha cambiato classe da {utenti[0][2]} a {str(messaggio)}. Data e ora: {roboAntiCrashPerEdit.date}")
        roboAntiCrashPerEdit.reply_text(f"Avevi già una classe impostata ({utenti[0][2]}), l'ho cambiata in {str(messaggio)}.")
    
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

        log(f"Inizio a mandare le variazioni agli utenti")

        utenti = ottieni_utenti()
        if len(utenti) != 0:
            for utente in utenti:
                if (giornoPrima and not utente[4]):
                    continue
                elif (not giornoPrima and not utente[3]):
                    continue

                id = utente[0]
                classe = utente[2]
                MandaVariazioni(
                    bot=bot,
                    classe=classe, 
                    giorno=("domani" if giornoPrima else "oggi"),
                    chatId=id
                    )
                log(f"Variazioni di {'domani' if giornoPrima else 'oggi'} mandate a: {utente[1]}")

def getLink(update: Update, context: CallbackContext):

    robaAntiCrashPerEdit = update.message if update.message != None else update.edited_message
    
    log(f"{update.message.from_user.name}, {update.message.from_user.id} ha fatto {robaAntiCrashPerEdit.text}")

    dati = robaAntiCrashPerEdit.text.lower().replace('/linkpdf ', '')

    datiList = dati.strip().split(" ")
    robaAntiCrashPerEdit.reply_text(variazioniFile.Main(datiList[0].upper().strip(),giorno = datiList[1].strip() if len(datiList) > 1 else "",onlyLink=True))


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
        variazioniOrario = f"{variazioniFile.Main(classe,giorno)}"
        variazioniAule = f"{variazioniFile.controllaVariazioniAule(classe,giorno)}"

        bot.send_message(chat_id=chatId, text=variazioniOrario, parse_mode='Markdown')
        if variazioniAule != '':
            bot.send_message(chat_id=chatId, text=variazioniAule, parse_mode='Markdown')

    except Exception as e:
        # robaAntiCrashPerEdit.reply_text('Messaggio non valido. Il formato è: /variazioni 3A GIORNO-MESE (giorno e mese a numero)')
        try: # Se l'utente ha bloccato il bot esplode tutto
            bot.send_message(chat_id=chatId,text="Qualcosa è andato storto, whoops. Nel dubbio riprova")
            bot.send_message(chat_id = ID_CANALE_LOG, text=f'{str(e)}')
            log(f'{str(e)}')
        except:
            pass

def discord(update: Update, context: CallbackContext, ):
    update.message.reply_text('Discord del Pascal: https://discord.gg/UmUu6ZNMJy')

def off(update: Update, context: CallbackContext):
    id = update.message.from_user.id

    global mycursor
    global mydb
    
    idInTabella = ottieniUtentiDaID(id=id)

    if len(idInTabella) == 0:
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha una classe. ({update.message.text}) Data e ora: {update.message.date}")
        update.message.reply_text(f"Non hai una classe impostata. Se hai provato a disattivare le notifiche non credo tu voglia impostare una classe, ma nel dubbio si fa con /impostaClasse")
        return

    database_connection()
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha rimosso il suo id dal database dell'inoltro alle {update.message.date}")
    mycursor.execute(f'UPDATE utenti SET notifiche_mattina=0 WHERE id=\"{id}\";')
    update.message.reply_text('Non riceverai più notifiche. Per riabilitare le notifiche devi rifare /impostaClasse.')
    mydb.commit()
    database_disconnection()

def backupUtenti():
    utenti = ottieni_utenti()
    
    with open('Roba sensibile/backupUtenti.txt','w') as f:
        for utente in utenti:
            for i,dato in enumerate(utente):
                f.write(str(dato) + (" - " if i != len(utente)-1 else "\n"))

def canale(update: Update, context: CallbackContext):
    update.message.reply_text('Canale del bot: https://t.me/+7EexVd-RIoIwZjc0')

def spegniNotifiche(update: Update, context: CallbackContext):
    if (not update.message.from_user.id in ADMINS):
        update.message.reply_text("Non hai il permesso!")
        log (f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha il permesso per \"{update.message.text}\" alle {update.message.date}")
        return
    
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    
    global MANDO
    MANDO = False
    
    update.message.reply_text("Notifiche spente per tutti gli utenti")

def accendiNotifiche(update: Update, context: CallbackContext):
    if (not update.message.from_user.id in ADMINS):
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
    
    global sent_pdfs
    
    # Per salvare i pdf già mandati in caso di riavvio del bot
    try: 
        with open("sent_pdfs.txt","r") as f:
            sent_pdfs = f.readline().split(' - ')[0:-1]
    except:
        open("sent_pdfs.txt","w").close()
        sent_pdfs = []
    
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

    dp.add_handler(CommandHandler('linkPdf', getLink))
    dp.add_handler(CommandHandler('canale', canale))

    dp.add_handler(CommandHandler('off',off))

    # Comandi admin
    dp.add_handler(CommandHandler('broadcast', broadcast))
    dp.add_handler(CommandHandler('accendiNotifiche', accendiNotifiche))
    dp.add_handler(CommandHandler('spegniNotifiche', spegniNotifiche))

    

    dp.add_handler(imposta_classe) # Comando per impostare la classe per le notifiche
    
    dp.add_error_handler(error) # In caso di errore:
    
    

    # TODO: Da sistemare, fa schifo

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

    schedule.every().day.at("00:00").do(variazioniFile.CancellaCartellaPdf) # TODO: Da riguardare, causa errore alla mattina
    schedule.every().day.at("00:00").do(backupUtenti)

    Thread(target=schedule_checker).start()

    Thread(target=check, args=[dp.bot]).start()

    updater.start_polling(timeout=200)
    updater.idle()

def mandaSeNonBloccato(bot: Bot, chat_id: str | int, text: str, parse_mode="Markdown"):
    try:
        bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    except Unauthorized as e:
        log(f"L'utente con id \"{chat_id}\" ha bloccato il bot oppure non lo ha mai avviato ({e.message})")

def ottieni_utenti() -> list[list[str]]:
    database_connection()
    mycursor.execute(f'SELECT * FROM utenti;')
    utenti: list[list[str]] = mycursor.fetchall()
    database_disconnection()

    return aggiustaUtenti(utenti)

def aggiustaUtenti(utenti):
    utenti_polished: list[list[str]] = []
    
    # TODO: Cambiare funzionamento database. Non più byte robi ma stringe "True" e "False"

    # Converto i bytearray in stringa
    for utente in utenti:
        utente_polished = []
        for dato in utente:
            if not type(dato) == bytearray:
                utente_polished.append(dato)
            else:
                utente_polished.append(bool(dato.decode()))
        utenti_polished.append(utente_polished)

    return utenti_polished

def ottieniUtentiDaID(id: str | int):
    database_connection()
    mycursor.execute(f'SELECT * FROM utenti WHERE id={str(id)}')
    utenti: list[list[str]] = mycursor.fetchall() # Potrei usare fetch e basta ma meh, meglio copia incolla ormai
    database_disconnection()

    utenti = aggiustaUtenti(utenti)
    return utenti

# DA QUA IN GIÙ PER CONTROLLO LIVE DELLE VARIAZIONI
URL = "https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/"

def get_pdf_hash(filepath):
    """
    Calcola l'hash del contenuto del pdf
    Thanks chat gpt
    """
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as pdf:
        buf = pdf.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = pdf.read(BLOCKSIZE)
    return hasher.hexdigest()

lastcheck = [""]
def check(bot):
    global lastcheck

    while True:
        if not MANDO: # Se le notifiche sono spente 
            continue  # Non fare nada.

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
            # print("Aspetto") # Non più necessario, sappiamo che funziona
            time.sleep(300) # 5 min
            continue
        else:
            lastcheck = mod
            ottieni_info(bot=bot, soup=soup)

def getGiorno(url: str):
    url = url[url.rindex('/')+1:]
    test = url.split('-')
    del test[0:3]
    giorno = test[0] + "-" + convertiMese(test[1].lower())
    return giorno

def convertiMese(mese: str):
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    for i,m in enumerate(mesi):
        if mese == m:
            i+=1
            return str(i) if i > 9 else '0' + str(i)

sent_pdfs: list[str] 
def ottieni_info(bot: Bot, soup = None): # Viene invocato se la pagina risulta essere stata cambiata
    if (soup == None): # check() lo chiama con il soup, così da non dover rifare la richiesta al sito e perdere tempo
        Ok = False
        while not Ok:
            try:
                response = requests.get(URL)
                soup = BeautifulSoup(response.text, 'html.parser')
                Ok = True
            except:
                Ok = False

    links = soup.find_all('a')

    for link in links: # Controlla tutti i link nella pagina
        if ('.pdf' in link.get('href', [])): # Se è un pdf
            pdfName = link.get('href',[])[link.get('href',[]).rindex("/")+1:]
            log("Downloading file: " + f"\"{pdfName}\"")
            
            Ok = False # Questo ciclo serve in caso esplode mentre fa la richiesta (Forse non necessario)
            while not Ok:
                try:
                    response = requests.get(link.get('href')) # Fa una richiesta al link e lo scarica
                    Ok = True
                except:
                    Ok = False
                
            pdfPath = "pdfScaricati/" + pdfName
            giorno = getGiorno(response.url)
            
            # Scrivi il contenuto del pdf scaricato in un file
            with open(pdfPath, 'wb') as pdf:
                pdf.write(response.content) 

            pdf_hash = get_pdf_hash(pdfPath) # Prendo l'hash per riconoscere il pdf in modo da non inviarlo ancora
                                             # Al prossimo cambiamento del sito. 
            
            global sent_pdfs
            
            if pdf_hash in sent_pdfs: # Se il pdf e gia stato inviato si ferma e passa al prossimo link
                continue
            
            sent_pdfs.append(pdf_hash)

            with open("sent_pdfs.txt","w") as f: # Salvataggio su file per poter riavviare il bot con tranquillità
                for k in sent_pdfs:
                    f.write(k + ' - ')

            for utente in ottieni_utenti():
                classe = utente[2]
                id = utente[0]

                avviso = f"Trovata una modifica sulle variazioni del `{giorno}`.\n(Potrebbe non cambiare nulla per la tua classe)\n\n"
                

                try: # try in caso la lettura del PDF fallisce
                    variazioniOrario = variazioniFile.LeggiPdf(pdfPath)
                except:
                    mandaSeNonBloccato(bot,chat_id=id, text=avviso+f"Qualcosa è andato storto nella lettura del pdf del giorno `{giorno}`.\n\nEcco il link:\n{link.get('href', [])}", parse_mode="Markdown")
                    log(f"Mandato errore pdf a {utente[1]}")
                    continue # Salta il resto del codice
                
                variazioniOrarioClasse = variazioniFile.CercaClasse(classe,variazioniOrario)
                stringa = variazioniFile.FormattaOutput(variazioniOrarioClasse,giorno=giorno,classe=classe)
                
                try:
                    mandaSeNonBloccato(bot,chat_id=id, text=avviso+stringa, parse_mode="Markdown")
                    log(f"Mandate variazioni {classe} a {utente[1]}")
                except:
                    pass

if __name__ == '__main__':
    main()