TOKEN = fromJSON('sensible/sensible.json')['token']  # TOKEN DEL BOT

CANALE_LOG = fromJSON('sensible/sensible.json')['canale_log'] # Se vuoi mandare i log del bot in un canale telegram, comodo a parere mio.

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

from db import query
from jsonUtils import fromJSON
from log import log

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): # /start
    await middleware(update,context)
    
    await log(f'{update.message.from_user.username}, {update.message.from_user.id} - Ha eseguito /start')
    await update.message.reply_text(f'Hai avviato il bot, congrats')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE): # /help
    await middleware(update,context)
    
    await log(f'{update.message.from_user.username}, {update.message.from_user.id} - Ha eseguito /help')

# Segnala quando il bot crasha, con motivo del crash
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log(f'Update "{update}" caused error "{context.error}"',context.bot, "error")

# Questa funzione sarà eseguita prima di tutte le altre e per ogni messaggio che non è un comando
async def middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.message.chat.type != 'channel':
        await update.effective_message.reply_text("Bot ancora in sviluppo.")
        
def main():
    # Avvia il bot
    application = Application.builder().token(TOKEN).build() # Se si vuole usare la PicklePersistance bisogna aggiungere dopo .token(TOKEN) anche .persistance(OGGETTO_PP)

    application.add_handler(MessageHandler(filters=filters.ALL & ~filters.COMMAND, callback=middleware))
    
    application.add_handler(CommandHandler("start", start)) # Aggiungi un command handler, stessa cosa per i conversation handler
    application.add_handler(CommandHandler("help", help))
    
    application.add_error_handler(error) # Definisce la funzione che gestisce gli errori
    
    jq = application.job_queue # Per eseguire funzioni asincrone con frequenza, ritardi o a pianificazione.
    
    application.run_polling() # Avvia il polling: https://blog.neurotech.africa/content/images/2023/06/telegram-polling-vs-webhook-5-.png 
    
# Stabilisce che il codice sarà avviato solo quando il file è aperto direttamente, e non da un altro programma
# (Devi avviare il .py direttamente, rendendolo così il __main__)
if __name__ == '__main__':
    main()