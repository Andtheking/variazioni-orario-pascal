
#region Telegram library
import telegram

from telegram.ext import (
    Application, # Per il bot
    CommandHandler, # Per i comandi
    MessageHandler, # Per i messaggi
    ConversationHandler, # Per più handler concatenati (Può salvare il suo stato con PicklePersistance)
    ContextTypes, # Per avere il tipo di context (ContextTypes.DEFAULT)
    CallbackQueryHandler, # Per gestire il click di un bottone o simile
    filters, # Per filtrare gli Handler 
    PicklePersistence # Per un ConversationHandler, vedi https://gist.github.com/aahnik/6c9dd519c61e718e4da5f0645aa11ada#file-tg_conv_bot-py-L9
)
from telegram import (
    Update, # È il tipo che usiamo nei parametri dei metodi
    
    User, # Tipo che rappresenta un Utente
    Message, # Tipo che rappresenta un Messaggio
    InlineKeyboardButton, # Per le tastiere
    InlineKeyboardMarkup, # Per le tastiere
    
)

from telegram.constants import (
    ParseMode, # Per assegnare il parametro "parse_mode=" nei messaggi che il bot invia
)
#endregion

from string import ascii_uppercase, ascii_lowercase, digits

from db import queryGet, queryGetSingleValue, queryInsert
from jsonUtils import fromJSON
from log import log, send_logs_channel

TOKEN = fromJSON('sensible/utils.json')['token']  # TOKEN DEL BOT
CANALE_LOG = fromJSON('sensible/utils.json')['canale_log'] # Se vuoi mandare i log del bot in un canale telegram, comodo a parere mio.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): # /start
    await doAlways(update,context)
    
    await update.message.reply_text(f'Hai avviato il bot, congrats')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE): # /help
    await doAlways(update,context)
    await update.message.reply_text("aiuto")

# Segnala quando il bot crasha, con motivo del crash
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(f'Update "{update}" caused error "{context.error}"',context.bot, "error")

# Questa funzione sarà eseguita prima di tutte le altre e per ogni messaggio che non è un comando
async def doAlways(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    
    if message.text[0] == '/':
        await log(f"{user.name} ha eseguito {message.text} alle {message.date}")
        
    # TODO: Se cambia qualcosa del profilo tg, il bot lo aggiorna
    if user is not None and len(queryGet(f"SELECT id FROM utenti WHERE id = ?;",(user.id,))) == 0:
        queryGet(f"INSERT INTO utenti (id, username) VALUES (?,?);",(user.id,user.name))
        await log(f"Inserito nel DB il seguente utente: {user.id},{user.name}", context.bot)
    
    return user,message


async def impostaClasse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user,message = await doAlways(update,context)
    inpt = context.matches[0].group(1) # Non serve controllo perché qua entra solo se è matchato
    
    if queryGetSingleValue("""--sql
        SELECT COUNT(*) 
        FROM utenti
        WHERE id = ? AND modalita = 'studente';
    """,(user.id,)) == 0:
        await message.reply_text("Devi essere in modalità studente. /modalita")
        return

    queryInsert("""--sql
        UPDATE utenti
        SET classe = ?
        WHERE id = ?;
    """,(inpt,user.id))
    await message.reply_text(f"Aggiunto in modalità studente con classe impostata a: {inpt}")

async def impostaClasseConversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

import re
def main():
    # Avvia il bot
    application = Application.builder().token(TOKEN).build() # Se si vuole usare la PicklePersistance bisogna aggiungere dopo .token(TOKEN) anche .persistance(OGGETTO_PP)

    imposta_classe = MessageHandler(filters.Regex(re.compile(r"[!.\/]impostaClasse\s+([1-5][A-Z])",re.IGNORECASE)),impostaClasse)
    
    application.add_handler(imposta_classe,0)
    
    application.add_handler(CommandHandler("start", start)) # Aggiungi un command handler, stessa cosa per i conversation handler
    application.add_handler(CommandHandler("help", help))
    
    
    application.add_handler(MessageHandler(filters=filters.ALL & ~filters.COMMAND, callback=doAlways),1)
    
    # imposta_classe_conv = ConversationHandler(
    #     entry_points=[CommandHandler("impostaClasse", impostaClasse)],
    #     states={
    #         0: [MessageHandler(filters.TEXT & ~ filters.COMMAND, ClasseImpostata)],
    #     },
    #     fallbacks=[CommandHandler('cancel', cancel)],
    # )

    # imposta_prof = ConversationHandler(
    #     entry_points=[CommandHandler("impostaProf", impostaProf)],
    #     states={
    #         0: [MessageHandler(filters.TEXT & ~ filters.COMMAND, ProfImpostato)],
    #     },
    #     fallbacks=[CommandHandler('cancel', cancel)],
    # )
    
    
    
    application.add_error_handler(error) # Definisce la funzione che gestisce gli errori
    
    jq = application.job_queue # Per eseguire funzioni asincrone con frequenza, ritardi o a pianificazione.
    
    jq.run_repeating(
        callback=send_logs_channel,
        interval=60
    )
    application.run_polling() # Avvia il polling: https://blog.neurotech.africa/content/images/2023/06/telegram-polling-vs-webhook-5-.png 
    
# Stabilisce che il codice sarà avviato solo quando il file è aperto direttamente, e non da un altro programma
# (Devi avviare il .py direttamente, rendendolo così il __main__)
if __name__ == '__main__':
    main()