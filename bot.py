
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

# Librerie esterne
import re

# Moduli interni
from utils.db import queryGet, queryGetSingleValue, queryNoReturn
from utils.jsonUtils import fromJSON
from utils.log import log, send_logs_channel



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
    log(f'Update "{update}" caused error "{context.error}"',context.bot, "error")

def cancel(action: str): 
    async def thing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user,message = await doAlways(update,context)
        await message.reply_text(f"Ok, azione \"{action}\" annullata")
        return ConversationHandler.END
    return thing


def setup_class_conv():
    imposta_classe_conv_entry = MessageHandler(filters.Regex(re.compile(r"^[!.\/]impostaClasse$",re.IGNORECASE)),impostaClasseConversation)
    imposta_classe_conv = ConversationHandler(
        entry_points=[imposta_classe_conv_entry],
        states={
            1: [
                MessageHandler(filters.Regex(re.compile(r"^([1-5][A-Z])$",re.IGNORECASE)),setClass),
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex(CANCEL_REGEX),cancel("imposta classe")), 
            MessageHandler(filters.TEXT & ~filters.COMMAND,class_format_error)
        ]
    )
    return imposta_classe_conv

def setup_prof_conv():
    imposta_prof_conv_entry = MessageHandler(filters.Regex(re.compile(r"^[!.\/]impostaProf$",re.IGNORECASE)),impostaProfConversation)
    imposta_prof_conv = ConversationHandler(
        entry_points=[imposta_prof_conv_entry],
        states={
            1: [
                MessageHandler(filters.Regex(re.compile(r"^(.+)$",re.IGNORECASE)),setProf),
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex(CANCEL_REGEX),cancel("imposta prof"))
        ]
    )
    return imposta_prof_conv


# Commands
from commands.impostaClasse import setClass, impostaClasse, impostaClasseConversation, class_format_error
from commands.impostaProf import setProf, impostaProf, impostaProfConversation

from commands.modalita import modalita

from commands.doAlways import doAlways

CANCEL_REGEX = re.compile(r"^[!.\/]cancel$",re.IGNORECASE)

bot = None

def main():
    # Avvia il bot
    application = Application.builder().token(TOKEN).build() # Se si vuole usare la PicklePersistance bisogna aggiungere dopo .token(TOKEN) anche .persistance(OGGETTO_PP)

    handlers = {
        "impostaClasse": MessageHandler(filters.Regex(re.compile(r"^[!.\/]impostaClasse\s+([1-5][A-Z])$",re.IGNORECASE)),impostaClasse),
        "impostaProf": MessageHandler(filters.Regex(re.compile(r"^[!.\/]impostaProf\s+(.+)$",re.IGNORECASE)),impostaProf),
        "modalita": MessageHandler(filters.Regex(re.compile(r"^[!.\/]modalit[aà]$")),modalita),
        "impostaClasseConversation": setup_class_conv(),
        "impostaProfConversation": setup_prof_conv(),
    }
    
    for v in handlers.values():
        application.add_handler(v,0)
    
    application.add_handler(CommandHandler("start", start)) # Aggiungi un command handler, stessa cosa per i conversation handler
    application.add_handler(CommandHandler("help", help))
    
    # Se non cadi in nessun handler, vieni qui
    application.add_handler(MessageHandler(filters=filters.ALL, callback=doAlways),1)
    
    application.add_error_handler(error) # Definisce la funzione che gestisce gli errori
    
    jq = application.job_queue # Per eseguire funzioni asincrone con frequenza, ritardi o a pianificazione.
    
    jq.run_repeating(
        callback=send_logs_channel,
        interval=60
    )
    
    global bot
    bot = application.bot
    application.run_polling() # Avvia il polling: https://blog.neurotech.africa/content/images/2023/06/telegram-polling-vs-webhook-5-.png 
    
# Stabilisce che il codice sarà avviato solo quando il file è aperto direttamente, e non da un altro programma
# (Devi avviare il .py direttamente, rendendolo così il __main__)
if __name__ == '__main__':
    main()