from requirements import *
from bot_requirements import * 

TOKEN = load_configs()['token']  # TOKEN DEL BOT
CANALE_LOG = load_configs()['canale_log'] # Se vuoi mandare i log del bot in un canale telegram, comodo a parere mio.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): # /start
    await update.message.reply_text(f'Hai avviato il bot, congrats')
    raise Exception("Prova")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE): # /help
    await update.message.reply_text("aiuto")

# Segnala quando il bot crasha, con motivo del crash
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log(f'Update "{update}" caused error "{context.error}"',True, "errore")

def cancel(action: str): 
    async def thing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text(f"Ok, azione \"{action}\" annullata")
        return ConversationHandler.END
    return thing

actual_commands = {}
def message_handler_as_command(command, other=None, strict=True):
    prefix = rf"^[!.\/]{command}(?P<botSignature>@{config.BOT_USERNAME})?"
    other_pattern = rf"(?P<params>(?:\s*" + (other or '') + "))" if other else ''
    final_pattern = prefix+other_pattern + ('$' if strict else '')
    
    if command not in actual_commands:
        actual_commands[command] = [final_pattern]
    else:
        actual_commands[command].append(final_pattern)
        
    return filters.Regex(re.compile(final_pattern,re.IGNORECASE))



def impostaClasseConversation():
    return ConversationHandler(
        entry_points=[MessageHandler(message_handler_as_command("impostaClasse","(?P<classe>[1-5](?:BIO|[A-z]))?"), middleware(impostaClasse))],
        states={
            1: [MessageHandler(filters.Regex(re.compile('(?P<classe>[1-5](?:BIO|[A-z]))',re.IGNORECASE)), callback=middleware(impostaClasse))]
        },
        fallbacks=[MessageHandler(message_handler_as_command('cancel'), callback=cancel('imposta classe'))]
    )
    
    
def get_handlers():
    handlers = {
        "start": MessageHandler(message_handler_as_command('start'),middleware(start)),
        "help": MessageHandler(message_handler_as_command('help'),middleware(help)),
        "addAdmin": MessageHandler(message_handler_as_command('addAdmin','(?P<candidate>.+)?'), middleware(addAdmin)),
        "removeAdmin": MessageHandler(message_handler_as_command('removeAdmin','(?P<candidate>.+)?'), middleware(removeAdmin)),
        
        "variazioni":MessageHandler(message_handler_as_command('variazioni',".+", strict=False), middleware(variazioni)), # Controllo regex nella funzione interna
        "classe": MessageHandler(message_handler_as_command('classe'), middleware(classe)),
        
        "impostaClasse": impostaClasseConversation(),
        "rimuoviClasse": MessageHandler(message_handler_as_command('rimuoviClasse'), middleware(rimuoviClasse))
    }
    
    return handlers

def setup_jobs(job_queue: JobQueue):
    if not load_configs()['test']:
        job_queue.run_repeating(
            callback=send_logs_channel,
            interval=60,
        )

    
    # 300 secondi = 5 minuti
    job_queue.run_repeating(
        callback=check_school_website,
        interval=300,
        first=1
    )



def main():
    # Avvia il bot
    application = Application.builder().token(TOKEN).build() # Se si vuole usare la PicklePersistance bisogna aggiungere dopo .token(TOKEN) anche .persistance(OGGETTO_PP)

    for v in get_handlers().values():
        application.add_handler(v,0)
    
    jq = application.job_queue # Per eseguire funzioni asincrone con frequenza, ritardi o a pianificazione.
    
    setup_jobs(jq)
    
    
    # Default handler per qualsiasi azione non gestita
    application.add_handler(MessageHandler(filters=filters.ALL, callback=middleware()),1)
    
    # Handler per la gestione degli errori
    application.add_error_handler(error)
    
    # Job eseguito appena il bot si accende
    jq.run_once(
        callback = initialize,
        when = 1
    )
    
    config.actual_commands = actual_commands

    application.run_polling() # Avvia il polling: https://blog.neurotech.africa/content/images/2023/06/telegram-polling-vs-webhook-5-.png 

# Stabilisce che il codice sarà avviato solo quando il file è aperto direttamente, e non come module
# (Devi avviare il .py direttamente, rendendolo così il __main__)
if __name__ == '__main__':
    main()