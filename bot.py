from requirements import *

TOKEN = load_configs()['token']  # TOKEN DEL BOT
CANALE_LOG = load_configs()['canale_log'] # Se vuoi mandare i log del bot in un canale telegram, comodo a parere mio.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): # /start
    await update.message.reply_text(f'Hai avviato il bot, congrats')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE): # /help
    await update.message.reply_text("aiuto")

# Segnala quando il bot crasha, con motivo del crash
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log(f'Update "{update}" caused error "{context.error}"',context.bot, "error")

def cancel(action: str): 
    async def thing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text(f"Ok, azione \"{action}\" annullata")
        return ConversationHandler.END
    return thing

def message_handler_as_command(command, other=None, strict=True):
    prefix = rf"^[!.\/]{command}(?P<botSignature>@{config.BOT_USERNAME})?"
    other_pattern = rf"(?P<params>(?:\s+" + (other or '') + "))?"
    final_pattern = prefix+other_pattern + ('$' if strict else '')
    print(final_pattern)
    return filters.Regex(re.compile(final_pattern,re.IGNORECASE))

def main():
    # Avvia il bot
    application = Application.builder().token(TOKEN).build() # Se si vuole usare la PicklePersistance bisogna aggiungere dopo .token(TOKEN) anche .persistance(OGGETTO_PP)

    print(message_handler_as_command('variazioni',other=r'(?:\s*(?P<classe>[1-5][A-Z]))?(?:\s*(?P<data>\d{1,2}[-/]\d{1,2}))?', strict=False).pattern.pattern)
    
    
    handlers = {
        "start": MessageHandler(message_handler_as_command('start'),middleware(start)),
        "help": MessageHandler(message_handler_as_command('help'),middleware(help)),
        "addAdmin": MessageHandler(message_handler_as_command('addAdmin','(?P<candidate>.+)?'), middleware(addAdmin)),
        "removeAdmin": MessageHandler(message_handler_as_command('removeAdmin','(?P<candidate>.+)?'), middleware(removeAdmin)),
        "variazioni":MessageHandler(message_handler_as_command('variazioni',".+", strict=False), middleware(variazioni)), # Controllo regex nella funzione interna
        "impostaClasse":MessageHandler(message_handler_as_command("impostaClasse","(?P<classe>[1-5][A-z])"), middleware(impostaClasse))
    }
    
    for v in handlers.values():
        application.add_handler(v,0)
    
    # Se non cadi in nessun handler, vieni qui
    application.add_handler(MessageHandler(filters=filters.ALL, callback=middleware()),1)
    
    application.add_error_handler(error) # Definisce la funzione che gestisce gli errori
    
    jq = application.job_queue # Per eseguire funzioni asincrone con frequenza, ritardi o a pianificazione.
    

    if not load_configs()['test']:
        jq.run_repeating(
            callback=send_logs_channel,
            interval=60
        )

    jq.run_once(
        callback = initialize,
        when = 1
    )
    
    # 300 secondi = 5 minuti
    jq.run_repeating(
        callback=check_school_website,
        interval=300,
        first=1
    )
    
    

    
    application.run_polling() # Avvia il polling: https://blog.neurotech.africa/content/images/2023/06/telegram-polling-vs-webhook-5-.png 
    
# Stabilisce che il codice sarà avviato solo quando il file è aperto direttamente, e non da un altro programma
# (Devi avviare il .py direttamente, rendendolo così il __main__)
if __name__ == '__main__':
    main()