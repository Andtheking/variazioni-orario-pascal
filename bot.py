TOKEN = None
MANDO = True

ID_CANALE_LOG = '-1001837249321'

with open("Roba sensibile/token.txt","r") as file:
    TOKEN = file.read().splitlines()[0]

import os
import hashlib
import logging
import re
from threading import Thread
from time import sleep
from bs4 import BeautifulSoup
import mysql.connector
import requests
import schedule

from telegram import (
    Bot, Message, Update, User,InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
    )
from telegram.error import Unauthorized, BadRequest

from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater, CallbackQueryHandler)

import python_scripts.variazioni.variazioni as variazioniFile

# Indici credenziali_database
# 0 = Host
# 1 = User
# 2 = Password
# 3 = Database

with open("Roba sensibile/database.txt","r") as file:
    credenziali_database = file.read().splitlines()

# PORT = int(os.environ.get('PORT','8443'))

CLASSE = 0
PROF = 0

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

days = "|oggi|domani"

#https://regex101.com/r/5s6yUW/1
rVarClasse = re.compile(r"(/variazioni) ?([1-5](?:[a-z]|bio))? ?(\b(?:(?:0[1-9]|[1-9])|[12][0-9]|3[01])\b(?:-|\/)\b(?:(0[1-9]|[1-9])|1[0-2])\b"+days+")?$")
rVarProf = re.compile(r"(/variazioni) ?(\D+?\D+?)? ?(\b(?:(?:0[1-9]|[1-9])|[12][0-9]|3[01])\b(?:-|\/)\b(?:(?:0[1-9]|[1-9])|1[0-2])\b"+days+")?$")
rImp = re.compile(r"^[1-5](?:[a-z]|[A-Z]|BIO)$")

def database_connection() -> mysql.connector.MySQLConnection:
    
    try:
        return mysql.connector.connect(
            host=credenziali_database[0],
            user=credenziali_database[1],
            password=credenziali_database[2],
            database=credenziali_database[3]
            )
    except:
        log("C'è stato un problema con la connessione al database")
        raise Exception("C'è stato un problema con la connessione al database")        

def database_disconnection(db: mysql.connector.MySQLConnection):
	db.disconnect() if db != None else log("Nessun database dalla quale disconnettersi")

import datetime

def log(messaggio: str, bot: Bot = None):
    messaggio = messaggio.replace("🟢","CERCHIO_VERDE_EMOJI")
    messaggio = messaggio.replace("🔴", "CERCHIO_ROSSO_EMOJI")

    logger.info(messaggio)
    with open('log.txt','a') as f:
        f.write(datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S,%f") + " - " + messaggio + "\n")

    if bot == None:
        return

    bot.send_message(chat_id=ID_CANALE_LOG,text=messaggio)
    
        
def help(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text(
        text="Questo bot ti permette di vedere le variazioni orario dell'ITI Pascal. (Sia per prof sia per studenti!)\n\n" +
        "- Il comando /variazioni che ti fornisce le variazioni (aule e orario) del giorno dopo che riguardano la classe o il prof impostato;\n" +
        "Se invece non hai impostato nulla, o vuoi vedere prof o classe diversa dalla tua puoi scrivere semplicemente <code>/variazioni [CLASSE o Cognome N.] [GIORNO-MESE]</code>.\n\n" +
        "- Imposta una classe cliccando /impostaClasse (o scrivendo la classe nello stesso messaggio tipo <code>/impostaClasse 4I</code>), per poi scrivere la classe nel formato \"1A-5Z\"" +
        "- Imposta un prof cliccando /impostaProf (o scrivendo il Cognome N. del prof tipo <code>/impostaProf Spirito F.</code>).\n<b>Attenzione</b> il bot non controlla se ciò che scrivi come prof sia giusto, se sbagli a scrivere riceverai semplicemente il messaggio \"Nessuna variazione per XXXX\"\n\n"
        "Una volta impostata una classe (o prof), oltre a non dover specificare nulla nel messaggio /variazioni, riceverai:\n" +
        "- Notifiche alle 6.30 con le variazioni del giorno e alle 21.00 con quelle del giorno dopo;\n" +
        "- Notifica all'uscire o alla modifica di un pdf, con le variazioni senza dover aprire il sito\n\n" + 
        "Se le notifiche ti danno fastidio e vuoi usare solo il comando /variazioni, puoi usare il comando /gestisciNotifiche\n\n"+
        "<b>Attenzione!</b> Una volta impostata la classe con /impostaClasse o /impostaProf gli amministratori del bot potranno vedere il tuo ID telegram, il tuo username, la tua classe (se impostata), il tuo prof (se impostato) e le preferenze delle notifiche.",
        parse_mode=ParseMode.HTML
    ) 

def start(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    update.message.reply_text("Versione 3.0. Per capire come funziona usa /help.")

def impostaClasse(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    id = update.message.from_user.id

    utenti = ottieniUtentiDaID(id)
    if (len(utenti) > 0):
        utente = utenti[0]
        if utente[7] != 'studente':
            update.message.reply_text("Devi essere in modalità studente. /modalita")
            return ConversationHandler.END
    
    classeDaImpostare = update.message.text.lower().replace("/impostaclasse","").strip().upper()
    
    if classeDaImpostare == "":
        update.message.reply_text("Mandami la classe nel formato \"1A\" oppure annulla con /cancel")
        if len(utenti) == 0:
            update.message.reply_text("<b>Attenzione!</b> una volta impostata la classe gli admin del bot potranno vedere:\n- ID utente\n- Username o nome\n- Classe\n- Preferenze notifiche\n- Modalità studente o prof\n- Prof selezionato",parse_mode=ParseMode.HTML)
        return CLASSE

    global rImp
    m = rImp.match(classeDaImpostare)

    if not m:
        update.message.reply_text("Non hai inserito una classe valida (1-5A-Z o 1-5a-z)")
        return ConversationHandler.END
    
    if len(utenti) == 0: 
        con = database_connection()
        mycursor = database_cursor(con=con)
        
        mycursor.execute("INSERT INTO utenti (id,username,classe,modalita) VALUES (%s,%s,%s,\"studente\")",
                         (id,update.message.from_user.name,classeDaImpostare,)
                         )
        con.commit()
        
        update.message.reply_text(f"Aggiunto in modalità studente con classe impostata a: {classeDaImpostare}")
        database_disconnection(con)
        
        return ConversationHandler.END

    utente = utenti[0]
    mod = utente[7]

    if (mod != 'studente'):
        update.message.reply_text("Non sei in modalità studente. /modalita")
        return ConversationHandler.END

    classeAttuale = utente[2]

    con = database_connection()
    mycursor = database_cursor(con)
   
    if (classeAttuale is None):  
        mycursor.execute('UPDATE utenti SET classe=%s WHERE id=%s;',(classeDaImpostare,id,))
        messaggio = f"Non avevi una classe impostata, imposto la: <code>{classeDaImpostare}</code>;"
    else:
        mycursor.execute('UPDATE utenti SET classe=%s WHERE id=%s;',(classeDaImpostare,id,))
        messaggio = f"Avevi già impostato: <code>{classeAttuale}</code>, imposto: <code>{classeDaImpostare}</code>;"
    
    con.commit()
    database_disconnection(con)


    update.message.reply_text(text=messaggio, parse_mode=ParseMode.HTML)

def database_cursor(con: mysql.connector.MySQLConnection):
    return con.cursor(prepared=True)

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
                text=update.message.text.replace("/broadcast ","") + f"\n\n~{ADMINS[update.message.from_user['id']]}",
                parse_mode=ParseMode.HTML
                )
            log(f"Messaggio inviato a {utente[1]}, {utente[0]}")
        
        log('Ho finito di mandare il messaggio agli utenti',contex.bot)
    else:
        update.message.reply_text("Non hai il permesso!")
        log("Ma non ha il permesso",contex.bot)

def ProfImpostato(update: Update, context: CallbackContext):
    id = update.message.from_user.id
    roboAntiCrashPerEdit = update.message if update.message is not None else update.edited_message
    messaggio = str(roboAntiCrashPerEdit.text).title()

    if '<' in messaggio or '>' in messaggio:
        roboAntiCrashPerEdit.reply_text("Non puoi inserire < o > nel messaggio. Riprova o /cancel")
        return

    if len(messaggio) <= 2:
        update.message.reply_text("Nome prof non valido, almeno 3 caratteri. Riprova o /cancel")
        return

    utenti = ottieniUtentiDaID(id=id)
    
    con = database_connection()
    mycursor = database_cursor(con)
    
    risposta = ""
    if len(utenti) == 0:
        
        mycursor.execute('INSERT utenti (id, username, modalita, prof) VALUES (%s,%s,\"prof\",%s);',(id,roboAntiCrashPerEdit.from_user.name,messaggio,))
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha impostato \"{messaggio}\" come prof alle {roboAntiCrashPerEdit.date}")
        risposta = f"Hai impostato <code>{roboAntiCrashPerEdit.text}</code> come prof.\n\nRiceverai una notifica alle 6.30 ogni mattina e alle 21:00 ogni sera con le variazioni orario. Per non ricevere più notifiche: /gestiscinotifiche"
    elif utenti[0][8] != "N/A":
        mycursor.execute('UPDATE utenti SET prof=%s WHERE id=%s;',(messaggio,id,))
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha cambiato prof in \"{messaggio}\" alle {roboAntiCrashPerEdit.date}")
        risposta = f"Avevi già un prof impostato (<code>{utenti[0][8]}</code>). Ho impostato <code>{messaggio}</code> come prof.\n\nRiceverai una notifica alle 6.30 ogni mattina e alle 21:00 ogni sera con le variazioni orario. Per non ricevere più notifiche: /gestiscinotifiche"
    else:
        mycursor.execute('UPDATE utenti SET prof=%s WHERE id=%s;',(messaggio,id,))
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha cambiato prof in \"{messaggio}\" alle {roboAntiCrashPerEdit.date}")
        risposta = f"Hai impostato \"{roboAntiCrashPerEdit.text}\" come prof.\n\nRiceverai una notifica alle 6.30 ogni mattina e alle 21:00 ogni sera con le variazioni orario. Per non ricevere più notifiche: /gestiscinotifiche"
    
    con.commit()
    database_disconnection(con)
    
    roboAntiCrashPerEdit.reply_text(risposta, parse_mode=ParseMode.HTML)
    return ConversationHandler.END
    

def ClasseImpostata(update: Update, context: CallbackContext):
    global mycursor
    global mydb
    global rImp

    id = update.message.from_user.id
    roboAntiCrashPerEdit = update.message if update.message is not None else update.edited_message
    classeDaImpostare = str(roboAntiCrashPerEdit.text).upper()
    
    m = rImp.match(classeDaImpostare)

    if not m:
        roboAntiCrashPerEdit.reply_text("Non hai inserito una classe valida (1-5A-Z o 1-5a-z o 1BIO)")
        return 
    
    utenti = ottieniUtentiDaID(id=id)
    risposta = ""
    
    con = database_connection()
    mycursor = database_cursor(con)
    
    if len(utenti) == 0:
        mycursor.execute('''
                         INSERT utenti (id, username, classe, modalita) 
                         VALUES (%s,%s,%s,\"studente\");
                         ''',
                         (str(id), roboAntiCrashPerEdit.from_user.name, classeDaImpostare,)
                         )
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha impostato \"{classeDaImpostare}\" come classe alle {roboAntiCrashPerEdit.date}")
        risposta = f"Hai impostato la classe <code>{classeDaImpostare}</code>.\n\nRiceverai una notifica alle 6.30 ogni mattina e alle 21:00 ogni sera con le variazioni orario. Per non ricevere più notifiche: /gestiscinotifiche"
    elif utenti[0][2] is not None:
        mycursor.execute('''
                         UPDATE utenti 
                         SET classe=%s 
                         WHERE id=%s;
                         ''',
                         (classeDaImpostare,str(id),)
                         )
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha cambiato classe in \"{classeDaImpostare}\" alle {roboAntiCrashPerEdit.date}")
        risposta = f"Avevi già una classe impostata (<code>{utenti[0][2]}</code>). Ho impostato la classe <code>{classeDaImpostare}</code>.\n\nRiceverai una notifica alle 6.30 ogni mattina e alle 21:00 ogni sera con le variazioni orario. Per non ricevere più notifiche: /gestiscinotifiche"
    else:
        mycursor.execute('''
                         UPDATE utenti 
                         SET classe=%s
                         WHERE id=%s;
                         ''',
                         (classeDaImpostare,id,)
                         )
        log(f"{roboAntiCrashPerEdit.from_user['name']}, {roboAntiCrashPerEdit.from_user['id']} ha cambiato classe in \"{classeDaImpostare}\" alle {roboAntiCrashPerEdit.date}")
        risposta = f"Hai impostato la classe \"{roboAntiCrashPerEdit.text}\".\n\nRiceverai una notifica alle 6.30 ogni mattina e alle 21:00 ogni sera con le variazioni orario. Per non ricevere più notifiche: /gestiscinotifiche"
        
    con.commit()
    database_disconnection(con)

    roboAntiCrashPerEdit.reply_text(risposta, parse_mode=ParseMode.HTML)

    return ConversationHandler.END

def classe(update: Update, context: CallbackContext):
    global mycursor
    id = update.message.from_user.id
    messaggio = update.message.text

    con = database_connection()
    mycursor = database_cursor(con)
    mycursor.execute(f'SELECT id, username, classe FROM utenti WHERE id={id};')
    idInTabella = mycursor.fetchall()
    database_disconnection(con)

    if len(idInTabella) == 0:
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha una classe. ({messaggio}) Data e ora: {update.message.date}")
        update.message.reply_text(f"Non hai una classe impostata. Impostala con /impostaClasse")

    elif idInTabella[0][2] != "None":
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha visto la sua classe alle {update.message.date}")
        update.message.reply_text(f"Classe attuale: {idInTabella[0][2]}")
    else:
        update.message.reply_text(f"Non hai una classe impostata")

def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    context.bot.send_message(ID_CANALE_LOG, text=f'{context.bot.name}\nUpdate "{update}" caused error "{context.error}')
    log(f'Update "{update}" caused error "{context.error}')

def cancel(update: Update, context: CallbackContext):
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha cancellato l'impostazione classe o prof alle {update.message.date}")
    update.message.reply_text("Azione annullata.")
    return ConversationHandler.END

def mandaMessaggio(sera: bool, bot: Bot):
    if MANDO:
        global mycursor

        log(f"Inizio a mandare le variazioni agli utenti")
        # 3: NOTIFICHE_MATTINA
        # 4: NOTIFICHE_SERA
        utenti = ottieni_utenti()
        if len(utenti) != 0:
            for utente in utenti:
                if (sera and not utente[4]): # Se è sera, e l'utente ha disabilitato la sera salta il ciclo
                    print(f"L'utente {utente[1]} ha disabilitato le notifiche serali")
                    continue
                elif (not sera and not utente[3]): # Se non è sera, e l'utente ha disabilitato la mattina, salta il ciclo
                    print(f"L'utente {utente[1]} ha disabilitato le notifiche mattutine")
                    continue
                prof = False
                if utente[7] == 'prof':
                    prof = True
                
                id = utente[0]
                classe = utente[2]
                sostituto = utente[8]
                if prof: # TODO: Trovare un modo per velocizzarlo, impiega troppo tempo.
                    MandaVariazioni(
                        bot=bot,
                        daCercare=sostituto, 
                        giorno=("domani" if sera else "oggi"),
                        chatId=id,
                        prof=prof)
                else:
                    MandaVariazioni(
                        bot=bot,
                        daCercare=classe, 
                        giorno=("domani" if sera else "oggi"),
                        chatId=id
                        )
                print(f"Variazioni di {'domani' if sera else 'oggi'} mandate a: {utente[1]}")
        log("Ho finito di mandare le variazioni")

rFormatoData = re.compile(r"(\b(?:(?:0[1-9]|[1-9])|[12][0-9]|3[01])\b(?:-|\/)\b(?:(?:0[1-9]|[1-9])|1[0-2])\b"+days+")")
def getLink(update: Update, context: CallbackContext):

    robaAntiCrashPerEdit = update.message if update.message != None else update.edited_message
    
    log(f"{robaAntiCrashPerEdit.from_user.name}, {robaAntiCrashPerEdit.from_user.id} ha fatto {robaAntiCrashPerEdit.text}")
    
    if '<' in robaAntiCrashPerEdit.text or '>' in robaAntiCrashPerEdit.text:
        robaAntiCrashPerEdit.reply_text("Non puoi inserire < o > nel messaggio.")
        return
    
    giorno = robaAntiCrashPerEdit.text.lower().replace('/linkpdf', '').strip()

    m = rFormatoData.match(giorno)
    
    links = variazioniFile.ottieniLinkPdf(giorno if m else "oggi")
    if links is None or links == []:
        robaAntiCrashPerEdit.reply_text(
            f"Non ho trovato nessun PDF per " + ((f"il {giorno}") if m else "oggi") + ". Prova a guardare sul sito:\n\nhttps://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/",
            disable_web_page_preview=True
        )
    else:
        robaAntiCrashPerEdit.reply_text(
            "\n\nTrovato un altro PDF con la stessa data:\n\n".join(links)
        )

ALIAS_GIORNI = ["","domani","oggi"]

def variazioni(update: Update, context: CallbackContext):
    global mycursor
    global rVarClasse
    global rVarProf
    
    robaAntiCrashPerEdit = update.message if update.message != None else update.edited_message
    messaggioNonValido = 'Messaggio non valido. Il formato è: /variazioni [3A o Cognome N.] [GIORNO-MESE] (giorno e mese a numero, domani se omessi)'
    
    id = robaAntiCrashPerEdit.from_user['id']

    log(f"{robaAntiCrashPerEdit.from_user['name']}, {robaAntiCrashPerEdit.from_user['id']} ha eseguito \"{robaAntiCrashPerEdit.text}\" alle {robaAntiCrashPerEdit.date}")
    
    if '<' in robaAntiCrashPerEdit.text or '>' in robaAntiCrashPerEdit.text:
        robaAntiCrashPerEdit.reply_text("Non puoi inserire < o > nel messaggio.")
        return
    
    m = rVarClasse.match(robaAntiCrashPerEdit.text.lower()) # deve matchare questo: https://regex101.com/r/fCC5e3/1
    
    prof = False
    if not m:
        m = rVarProf.match(robaAntiCrashPerEdit.text.lower())
        prof = True
        if not m:
            robaAntiCrashPerEdit.reply_text(messaggioNonValido)
            return

    daCercare = m.group(2)

    if daCercare is None:
        utenti = ottieniUtentiDaID(id)
        if len(utenti) == 0:
            robaAntiCrashPerEdit.reply_text("Devi specificare per forza un prof o una classe se non sei registrato (<code>/variazioni [CLASSE o COGNOME. N.] [GIORNO]</code>)",parse_mode=ParseMode.HTML)
            return
        utente = utenti[0]
        if utente[7] == 'prof':
            prof = True
            daCercare = utente[8]
        elif utente[7] == 'studente':
            daCercare = utente[2]
            if daCercare is None:
                robaAntiCrashPerEdit.reply_text("Non hai una classe impostata, impostala con /impostaClasse oppure usa il comando intero (<code>/variazioni [CLASSE o COGNOME. N.] [GIORNO]</code>)",parse_mode=ParseMode.HTML)
                return

    giorno = m.group(3)
    giorno = "domani" if giorno is None else giorno
    id = robaAntiCrashPerEdit.from_user.id

    if not prof:
        MandaVariazioni(context.bot, daCercare.upper(), giorno, id)
    else:
        MandaVariazioni(context.bot, daCercare.strip().title(), giorno, id, prof=True)


def MandaVariazioni(bot: Bot, daCercare: str, giorno: str, chatId: int, prof=False):
    
    try:
        variazioniOrario = f"{variazioniFile.Main(daCercare,giorno,prof=prof)}"
        
        variazioniAule = ""
        if not prof:
            variazioniAule = f"{variazioniFile.controllaVariazioniAuleClasse(daCercare,giorno)}"

        bot.send_message(chat_id=chatId, text=variazioniOrario, parse_mode=ParseMode.HTML,disable_web_page_preview=True)
        if variazioniAule != '':
            bot.send_message(chat_id=chatId, text=variazioniAule, parse_mode=ParseMode.HTML)

    except Exception as e:
        # robaAntiCrashPerEdit.reply_text('Messaggio non valido. Il formato è: /variazioni 3A GIORNO-MESE (giorno e mese a numero)')
        try: # Se l'utente ha bloccato il bot esplode tutto
            log(f'{str(e)}')
            bot.send_message(chat_id=chatId,text="Qualcosa è andato storto, whoops. Nel dubbio riprova")
            bot.send_message(chat_id = ID_CANALE_LOG, text=f'{str(e)}')
        except:
            pass

def gestisciNotifiche(update: Update, context: CallbackContext):
    robaAntiCrashPerEdit = update.message if update.message != None else update.edited_message
    id = robaAntiCrashPerEdit.from_user.id
    log(f"{robaAntiCrashPerEdit.from_user['name']}, {robaAntiCrashPerEdit.from_user['id']} ha eseguito \"{robaAntiCrashPerEdit.text}\" alle {robaAntiCrashPerEdit.date}")

    global mycursor
    global mydb
    
    utenti = ottieniUtentiDaID(id=id)

    if len(utenti) == 0:
        log(f"{robaAntiCrashPerEdit.from_user['name']}, {robaAntiCrashPerEdit.from_user['id']} non ha una classe. ({robaAntiCrashPerEdit.text}) Data e ora: {robaAntiCrashPerEdit.date}")
        robaAntiCrashPerEdit.reply_text(f"Non hai una classe impostata. Se hai provato a disattivare le notifiche non credo tu voglia impostare una classe, ma nel dubbio si fa con /impostaClasse")
        return
    utente = utenti[0]

    
    keyboard = ottieniTastieraNotifiche(utente=utente)
    robaAntiCrashPerEdit.reply_text("Ecco le impostazioni notifiche",reply_markup=InlineKeyboardMarkup(keyboard))

def ottieniTastieraNotifiche(utente) -> list[list[InlineKeyboardButton]]:
    opzioni_notifiche = {
        "mattina":"🔴" if not utente[3] else "🟢",
        "sera":"🔴" if not utente[4] else "🟢",
        "live":"🔴" if not utente[5] else "🟢",
        "nessunaVar":"🔴" if not utente[6] else "🟢",
    }

    keyboard = [
        [ # Riga 1
            InlineKeyboardButton(text="Notifiche mattina " + opzioni_notifiche["mattina"], callback_data='mattina'),
            InlineKeyboardButton(text="Notifiche sera " + opzioni_notifiche["sera"], callback_data='sera')
        ],
        [ # Riga 2
            InlineKeyboardButton(text="Notifiche live " + opzioni_notifiche["live"], callback_data='live'),
        ],
        [ # Riga 3
            InlineKeyboardButton(text="Notifiche con nessuna variazione " + opzioni_notifiche["nessunaVar"], callback_data='nessunaVar'),
        ]
    ]
    return keyboard

def bottoneNotificaPremuto(update: Update, context: CallbackContext):
    global mydb
    global mycursor
    
    query = update.callback_query
    tipo_notifica = update.callback_query.data

    

    utenti = ottieniUtentiDaID(update.callback_query.from_user.id)
    utente = utenti[0]

    risposta = ""

    con = database_connection()
    mycursor = database_cursor(con)
    if tipo_notifica == "mattina":
        mycursor.execute(f'UPDATE utenti SET notifiche_mattina = \"{str(not utente[3])}\" WHERE id=\"{utente[0]}\";')
        risposta = "Notifiche mattina " + ('accese.' if not utente[3] else 'spente.')
    elif tipo_notifica == "sera":
        mycursor.execute(f'UPDATE utenti SET notifiche_sera = \"{str(not utente[4])}\" WHERE id=\"{utente[0]}\";')
        risposta = "Notifiche sera " + ('accese.' if not utente[4] else 'spente.')
    elif tipo_notifica == "live":
        mycursor.execute(f'UPDATE utenti SET notifiche_live = \"{str(not utente[5])}\" WHERE id=\"{utente[0]}\";')
        risposta = "Notifiche live " + ('accese.' if not utente[5] else 'spente.')
    elif tipo_notifica == "nessunaVar":
        mycursor.execute(f'UPDATE utenti SET notifiche_nessunaVar = \"{str(not utente[6])}\" WHERE id=\"{utente[0]}\";')
        risposta = "Notifiche con nessuna variazione " + ('accese.' if not utente[6] else 'spente.')
    con.commit()
    database_disconnection(con)

    utente = ottieniUtentiDaID(update.callback_query.from_user.id)[0]
    query.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(
            ottieniTastieraNotifiche(utente=utente)
        )
    )
    query.answer(risposta)
    log(f"{utente[1]}, {utente[0]} ha cambiato le sue notifiche: {risposta}")

def backupUtenti():
    utenti = ottieni_utenti()
    
    if not os.path.exists('Roba sensibile/backupUtenti.txt'):
        open('Roba sensibile/backupUtenti.txt','w').close()

    with open('Roba sensibile/backupUtenti.txt','a') as f:
        for utente in utenti:
            for i,dato in enumerate(utente):
                f.write(str(dato) + (" - " if i != len(utente)-1 else "\n"))
        f.write("\n------------------\n\n")

def spegniNotifiche(update: Update, context: CallbackContext):
    if (not update.message.from_user.id in ADMINS):
        update.message.reply_text("Non hai il permesso!")
        log (f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha il permesso per \"{update.message.text}\" alle {update.message.date}")
        return
    
    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")
    
    global MANDO
    MANDO = False
    
    with open('Roba sensibile/settings.txt','w') as f:
        f.write("0")
    
    
    update.message.reply_text("Notifiche spente per tutti gli utenti")

def accendiNotifiche(update: Update, context: CallbackContext):
    if (not update.message.from_user.id in ADMINS):
        log (f"{update.message.from_user['name']}, {update.message.from_user['id']} non ha il permesso per \"{update.message.text}\" alle {update.message.date}")
        update.message.reply_text("Non hai il permesso!")
        return

    log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha eseguito \"{update.message.text}\" alle {update.message.date}")

    global MANDO
    MANDO = True
    
    with open('Roba sensibile/settings.txt','w') as f:
        f.write("1")
    
    update.message.reply_text("Notifiche accese per tutti gli utenti")

def cancellami(update: Update, context: CallbackContext):
    robaAntiCrashPerEdit = update.message if update.message is not None else update.edited_message
    id = robaAntiCrashPerEdit.from_user.id
    global mycursor

    utenti = ottieniUtentiDaID(id)

    if len(utenti) == 0:
        robaAntiCrashPerEdit.reply_text(f"Non hai una classe impostata. Se hai provato a cancellarti non credo tu voglia impostare una classe, ma nel dubbio si fa con /impostaClasse")
        log(f"{robaAntiCrashPerEdit.from_user['name']}, {robaAntiCrashPerEdit.from_user['id']} non ha una classe. ({robaAntiCrashPerEdit.text}) Data e ora: {robaAntiCrashPerEdit.date}")
    else:
        mydb = database_connection()
        mycursor = database_cursor(mydb)
        mycursor.execute(f'DELETE FROM utenti WHERE id=\"{id}\";')
        mydb.commit()
        database_disconnection(mydb)
        robaAntiCrashPerEdit.reply_text('Cancellato con successo dalla lista utenti del bot. Non riceverai più notifiche e per re-iscriverti dovrai rifare il comando /impostaClasse. (Le notifiche torneranno tutte attive)')
        log(f"{robaAntiCrashPerEdit.from_user['name']}, {robaAntiCrashPerEdit.from_user['id']} ha rimosso il suo id dal database alle {robaAntiCrashPerEdit.date}")

def cambia_modalita(update: Update, context: CallbackContext):
    robaAntiCrashPerEdit = update.message if update.message is not None else update.edited_message
    id = robaAntiCrashPerEdit.from_user.id
    log(f"{robaAntiCrashPerEdit.from_user['name']}, {robaAntiCrashPerEdit.from_user['id']} ha eseguito \"{robaAntiCrashPerEdit.text}\" alle {robaAntiCrashPerEdit.date}")

    utenti = ottieniUtentiDaID(id)

    if len(utenti) == 0: 
        robaAntiCrashPerEdit.reply_text("Non sei registrato. /impostaClasse")
        return

    utente = utenti[0]
    
    mod = utente[7]

    messaggio = ""

    mydb = database_connection()
    mycursor = database_cursor(mydb)
    if mod == 'studente':
        mycursor.execute(f'UPDATE utenti SET modalita=\"prof\" WHERE id=\"{id}\";')
        mydb.commit()
        messaggio = "Modalità cambiata in prof. Ora riceverai le notifiche in base ai sostituti e non alle classi"
    elif mod == 'prof':
        mycursor.execute(f'UPDATE utenti SET modalita=\"studente\" WHERE id=\"{id}\";')
        mydb.commit()
        messaggio = "Modalità cambiata in studente. Ora riceverai le notifiche in base alle classi e non ai sostituti"
        if utente[2] is None:
            messaggio += ". Attenzione, non hai una classe impostata. Ciò significa che non riceverai nessuna notifica. Impostane una con /impostaClasse."
        
    database_disconnection(mydb)
    
    robaAntiCrashPerEdit.reply_text(text=messaggio)

def impostaProf(update: Update, context: CallbackContext):
    robaAntiCrashPerEdit = update.message if update.message is not None else update.edited_message
    log(f"{robaAntiCrashPerEdit.from_user['name']}, {robaAntiCrashPerEdit.from_user['id']} ha eseguito \"{robaAntiCrashPerEdit.text}\" alle {robaAntiCrashPerEdit.date}")
    id = robaAntiCrashPerEdit.from_user.id

    profScelto = robaAntiCrashPerEdit.text.lower().replace("/impostaprof","").strip().title()
    
    utenti = ottieniUtentiDaID(id)
    
    if len(profScelto)== 0:
        if len(utenti) != 0 and utenti[0][7] == "studente":
            update.message.reply_text("Devi essere in modalità prof. /modalita")
            return ConversationHandler.END
        update.message.reply_text("Mandami il prof nel formato \"Cognome N.\" oppure annulla con /cancel (È a tua discrezione scrivere un prof valido.)")
        if len(utenti) == 0:
            update.message.reply_text("<b>Attenzione!</b> una volta impostata la classe gli admin del bot potranno vedere:\n- ID utente\n- Username o nome\n- Classe\n- Preferenze notifiche\n- Modalità studente o prof\n- Prof selezionato",parse_mode=ParseMode.HTML)
        return PROF

    elif len(profScelto) <= 2:
        robaAntiCrashPerEdit.reply_text("Nome prof non valido, almeno 3 caratteri.")
        return ConversationHandler.END


    if len(utenti) == 0: 
        mydb = database_connection()
        mycursor = database_cursor(mydb)
        mycursor.execute("""
                         INSERT INTO utenti (id,username,modalita,prof) 
                         VALUES (%s,%s,\"prof\",%s)""",
                         (id,robaAntiCrashPerEdit.from_user.name, profScelto,)
                    )
        mydb.commit()
        robaAntiCrashPerEdit.reply_text(f"Aggiunto in modalità professore con prof impostato a: {profScelto}")
        database_disconnection(mydb)
        return ConversationHandler.END

    utente = utenti[0]
    mod = utente[7]

    if (mod != 'prof'):
        robaAntiCrashPerEdit.reply_text("Non sei in modalità prof.")
        return ConversationHandler.END

    profAttuale = utente[8]

    mydb = database_connection()
    mycursor = database_cursor(mydb)
    if (profAttuale == "N/A"): # 
        mycursor.execute('UPDATE utenti SET prof=%s WHERE id=%s;',(profScelto,id,))
        mydb.commit()
        messaggio = f"Non avevi un prof impostato, imposto: <code>{profScelto}</code>; (Deve essere nel formato Cognome N.)"
    else:
        mycursor.execute('UPDATE utenti SET prof=%s WHERE id=%s;',(profScelto,id,))
        mydb.commit()
        messaggio = f"Avevi già impostato: <code>{profAttuale}</code>, imposto: <code>{profScelto}</code>; (Deve essere solo il cognome)"
    database_disconnection(mydb)


    robaAntiCrashPerEdit.reply_text(text=messaggio, parse_mode=ParseMode.HTML)
    

def main():
    if not os.path.exists('Roba sensibile/settings.txt'):
        f = open('Roba sensibile/settings.txt','w')
        f.write("1")
        f.close()
    
    with open('Roba sensibile/settings.txt','r') as f:
        global MANDO
        val = f.readline()
        MANDO = True if val == '1' else False
    
    
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

    imposta_prof = ConversationHandler(
        entry_points=[CommandHandler("impostaProf", impostaProf)],
        states={
            PROF: [MessageHandler(Filters.text & ~ Filters.command, ProfImpostato)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    # dp.add_handler(CommandHandler("impostaProf", impostaProf))
    
    dp.add_handler(CommandHandler("start", start)) 
    dp.add_handler(CommandHandler("help", help)) # Aiuto su come si usa il bot

    dp.add_handler(CommandHandler('classe', classe)) # Visualizza la classe che hai scelto per le notifiche la mattina

    dp.add_handler(CommandHandler('variazioni', variazioni, run_async=True)) # Visualizza variazioni di un'altra classe del giorno

    dp.add_handler(CommandHandler('linkPdf', getLink))

    dp.add_handler(CommandHandler('gestisciNotifiche',gestisciNotifiche))
    dp.add_handler(CallbackQueryHandler(bottoneNotificaPremuto))
    dp.add_handler(CommandHandler('cancellami', cancellami))

    dp.add_handler(CommandHandler("modalita", cambia_modalita))
    # dp.add_handler(CommandHandler("variazioniProf",variazioniProf))

    # Comandi admin
    dp.add_handler(CommandHandler('broadcast', broadcast))
    dp.add_handler(CommandHandler('accendiNotifiche', accendiNotifiche))
    dp.add_handler(CommandHandler('spegniNotifiche', spegniNotifiche))

    dp.add_handler(CommandHandler('log',send_logs))
    dp.add_handler(CommandHandler('listaUtenti',get_users))
    

    dp.add_handler(imposta_classe) # Comando per impostare la classe per le notifiche
    dp.add_handler(imposta_prof)

    dp.add_error_handler(error) # In caso di errore


    backupUtenti()
    
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

    schedule.every().day.at("07:00").do(variazioniFile.CancellaCartellaPdf)
    schedule.every().day.at("00:00").do(backupUtenti)

    Thread(target=check, args=[dp.bot]).start()

    Thread(target=schedule_checker).start()

    updater.start_polling(timeout=200)
    updater.idle()

def mandaSeNonBloccato(bot: Bot, chat_id, text: str, parse_mode=ParseMode.HTML):
    try:
        bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    except Unauthorized as e:
        log(f"L'utente con id \"{chat_id}\" ha bloccato il bot oppure non lo ha mai avviato ({e.message})")
    except BadRequest as e:
        pass

def ottieni_utenti() -> list[list[str]]:
    '''
    Ritorna una lista tipo\n
    [
            
        [
            [0] ID_UTENTE,\n
            [1] USERNAME,\n
            [2] CLASSE,\n
            [3] NOTIFICHE_MATTINA,\n
            [4] NOTIFICHE_SERA, \n
            [5] NOTIFICHE_LIVE,\n
            [6] NOTIFICHE_NESSUNAVAR\n
            [7] MODALITA (DEFAULT STUDENTE)\n
            [8] PROF (DEFAULT N/A)\n
        ]
    ]
    '''
    mydb = database_connection()
    mycursor = database_cursor(mydb)
    mycursor.execute(f'SELECT * FROM utenti;')
    utenti: list[list[str]] = mycursor.fetchall()
    database_disconnection(mydb)

    return aggiustaUtenti(utenti)

def aggiustaUtenti(utenti):
    utenti_polished: list[list[str]] = []

    # Converto le stringe in booleani
    for utente in utenti:
        utente_polished = []
        for dato in utente:
            if (dato == 'True'):
                utente_polished.append(True)
            elif (dato == 'False'):
                utente_polished.append(False)
            else:
                utente_polished.append(dato)
        utenti_polished.append(utente_polished)

    return utenti_polished

def ottieniUtentiDaID(id):
    '''
    Ritorna una lista tipo\n
    [
            
        [
            [0] ID_UTENTE,\n
            [1] USERNAME,\n
            [2] CLASSE,\n
            [3] NOTIFICHE_MATTINA,\n
            [4] NOTIFICHE_SERA, \n
            [5] NOTIFICHE_LIVE,\n
            [6] NOTIFICHE_NESSUNAVAR\n
            [7] MODALITA (DEFAULT STUDENTE)\n
            [8] PROF (DEFAULT N/A)\n
        ]
    ]
    '''

    mydb = database_connection()
    mycursor = database_cursor(mydb)
    mycursor.execute(f'SELECT * FROM utenti WHERE id={str(id)}')
    utenti: list[list[str]] = mycursor.fetchall() # Potrei usare fetch e basta ma meh, meglio copia incolla ormai
    database_disconnection(mydb)

    utenti = aggiustaUtenti(utenti)
    return utenti

# TODO: Spostare in file separato
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
            sleep(300) # 5 min
            continue
        else:
            lastcheck = mod
            ottieni_info(bot=bot, soup=soup)

def getGiorno(url: str):
    url = url[url.rindex('/')+1:].replace(".pdf","")
    test = url.split('-')
    del test[0:3]
    giorno = (test[0] if len(test[0]) > 1 else '0'+test[0]) + "-" + convertiMese(test[1].lower())
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

    variazioniAule = variazioniFile.leggiTutteVariazioniAule()

    for link in links: # Controlla tutti i link nella pagina
        if ('.pdf' not in link.get('href', [])): # Se è un pdf
            continue
        if ("aule" in link.get('href', [])):
            continue

        pdfName = link.get('href',[])[link.get('href',[]).rindex("/")+1:]
        log("Downloading file: " + f"\"{pdfName}\"")
        
        response = requests.get(link.get('href')) # Fa una richiesta al link e lo scarica
            
        pdfPath = "pdfScaricati/" + pdfName
        giorno = getGiorno(response.url)
        
        # Scrivi il contenuto del pdf scaricato in un file
        with open(pdfPath, 'wb') as pdf:
            pdf.write(response.content) 

        pdf_hash = get_pdf_hash(pdfPath) # Prendo l'hash per riconoscere il pdf in modo da non inviarlo ancora
                                         # al prossimo cambiamento del sito. 
        
        global sent_pdfs
        
        if pdf_hash in sent_pdfs: # Se il pdf è già stato inviato si ferma e passa al prossimo link
            continue
        
        sent_pdfs.append(pdf_hash)

        with open("sent_pdfs.txt","w") as f: # Salvataggio su file per poter riavviare il bot con tranquillità
            for k in sent_pdfs:
                f.write(k + ' - ')

        errore = False
        avviso = f"Trovata una modifica sulle variazioni del <code>{giorno}</code>.\n(Potrebbe non cambiare nulla per la tua classe)\n\n"
        
        try: # try in caso la lettura del PDF fallisce
            variazioniOrario = variazioniFile.LeggiPdf(pdfPath)
        except Exception as e:
            errore = True
            log(f"Errore: {e}", bot=bot)
            messaggioErrore = avviso+f"Qualcosa è andato storto nella lettura del pdf del giorno <code>{giorno}</code>.\n\nEcco il link:\n{link.get('href', [])}"
        
        if not MANDO: # Se le notifiche sono spente 
            continue  # Non fare nada.
        
        for utente in ottieni_utenti():
            classe = utente[2]
            modalita = utente[7].lower()
            sostituto = utente[8]
            

            id = utente[0]

            if (not utente[5]):
                print(f"L'utente {utente[1]} ha disabilitato le notifiche live")
                continue
            

            if errore:
                mandaSeNonBloccato(bot,chat_id=id, text=messaggioErrore, parse_mode=ParseMode.HTML)
                print(f"Mandato errore pdf a {utente[1]}")
                continue
            
            variazioniOrarioDaMandare = []
            stringa = ""
            if (modalita == "studente"): 
                if classe is None:
                    continue
                variazioniOrarioDaMandare = variazioniFile.CercaClasse(classe,variazioniOrario)
                variazioniAuleClasse = variazioniFile.controllaVariazioniAuleClasse(classe,giorno,variazioniAule)
                stringa = variazioniFile.FormattaOutput(variazioniOrarioDaMandare,giorno=giorno,classeOProf=classe)
            elif (modalita == "prof"):
                if sostituto == "N/A":
                    continue                    
                variazioniOrarioDaMandare = variazioniFile.CercaSostituto(sostituto=sostituto, docentiAssenti=variazioniOrario)
                stringa = variazioniFile.FormattaOutput(variazioniOrarioDaMandare,giorno,sostituto)

            

            if (not utente[6] and "Nessuna" in stringa):
                print(f"L'utente {utente[1]} ha disabilitato le notifiche live con nessuna variazione")
                continue
            
            try:
                mandaSeNonBloccato(bot,chat_id=id, text=avviso+stringa, parse_mode=ParseMode.HTML)
                if variazioniAuleClasse != "":
                    mandaSeNonBloccato(bot,chat_id=id, text=variazioniAuleClasse)
                print(f"Mandate variazioni {classe if utente[7] == 'studente' else sostituto} a {utente[1]}")
            except:
                pass

def send_logs(update: Update, context: CallbackContext):
    
    id = update.message.from_user.id
    if id in ADMINS:
        try:
            with open("log.txt","rb") as f:
                name = f"pascalBotLog {datetime.datetime.now().strftime(r'%Y-%m-%d %H;%M;%S')}.txt"
                update.message.reply_document(document=f,filename=name)
                
            with open("log2.txt","rb") as f:
                name = f"pascalBotLog2 {datetime.datetime.now().strftime(r'%Y-%m-%d %H;%M;%S')}.txt"
                update.message.reply_document(document=f,filename=name)
        except Exception as e:
            log(e)
            pass
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha preso i log alle {update.message.date}")
    else:
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha provato ad accedere ai log alle {update.message.date}")

def get_users(update: Update, context: CallbackContext):
    id = update.message.from_user.id
    if id in ADMINS:
        backupUtenti()

        with open('Roba sensibile/backupUtenti.txt','r') as f:
            stringa = f.read()
        lista_utenti = stringa.split("------------------")[-2].split("\n")
        with open('Roba sensibile/lista_utenti.txt','w') as f:
            f.write("\n".join([k for k in lista_utenti if k != ""]))

        name = f"pascalUserList {datetime.datetime.now().strftime(r'%Y-%m-%d %H;%M;%S')}.txt"
        update.message.reply_document(document=open("Roba sensibile/lista_utenti.txt",'rb'), parse_mode=ParseMode.HTML, filename=name)
        update.message.reply_text(text=f"Numero utenti: {len([k for k in lista_utenti if k != ''])}", parse_mode=ParseMode.HTML)
        os.remove("Roba sensibile/lista_utenti.txt")
        
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha visto tutti gli utenti alle {update.message.date}")
    else:
        log(f"{update.message.from_user['name']}, {update.message.from_user['id']} ha provato a vedere tutti gli utenti alle {update.message.date}")


if __name__ == '__main__':
    main()
