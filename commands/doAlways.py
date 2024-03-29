from telegram import Update
from telegram.ext import ContextTypes

from utils.log import log
from utils.db import queryGet

# Questa funzione sarà eseguita prima di tutte le altre e per ogni messaggio che non è un comando
async def doAlways(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    
    if message.text[0] == '/':
        log(f"{user.name} ha eseguito {message.text} alle {message.date}")
        
    # TODO: Se cambia qualcosa del profilo tg, il bot lo aggiorna
    if user is not None and len(queryGet(f"SELECT id FROM utenti WHERE id = ?;",(user.id,))) == 0:
        queryGet(f"INSERT INTO utenti (id, username) VALUES (?,?);",(user.id,user.name))
        log(f"Inserito nel DB il seguente utente: {user.id},{user.name}", context.bot)
    
    return user,message