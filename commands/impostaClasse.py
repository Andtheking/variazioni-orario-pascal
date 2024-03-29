from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .doAlways import doAlways
from utils.db import queryGetSingleValue, queryNoReturn


async def impostaClasse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user,message = await doAlways(update,context)
    inpt = context.matches[0].group(1) # Non serve controllo perché qua entra solo se è matchato

    change_class(inpt,user.id)
    await message.reply_text(f"Classe impostata a: {inpt}")

async def impostaClasseConversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user,message = await doAlways(update,context)
    
    await message.reply_text("Scrivi ora la classe nel formato \"1A\"")
    return 1

async def setClass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Sarà eseguito sempre dopo impostaClasseConversation, non servirebbe fare doAlways, 
    # però meglio farlo così se qualcuno cambia nickname nel mentre il bot lo tiene in considerazione
    user,message = await doAlways(update,context)
    inpt = context.matches[0].group(1)
    
    change_class(inpt, user.id) # Non serve controllo perché qua entra solo se è matchato
    
    await message.reply_text(f"Classe impostata a: {inpt}")
    return ConversationHandler.END
    
async def class_format_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user,message = await doAlways(update,context)

    await message.reply_text("Formato classe non valido. Invia un messaggio che contiene solo la classe in formato \"1A\" o annulla con /cancel")
    return 1

def change_class(inpt, user):
    queryNoReturn("""--sql
        UPDATE utenti
        SET classe = ?, modalita = 'studente'
        WHERE id = ?;
    """,(inpt,user))

