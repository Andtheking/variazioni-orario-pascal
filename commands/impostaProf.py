from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .doAlways import doAlways
from utils.db import queryGetSingleValue, queryNoReturn


async def impostaProf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user,message = await doAlways(update,context)
    inpt = context.matches[0].group(1) # Non serve controllo perché qua entra solo se è matchato

    change_prof(inpt,user.id)
    await message.reply_text(f"Prof impostato a: {inpt} (Il bot non verifica la correttezza di questo, se sbagli non riceverai notifiche.)")

async def impostaProfConversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user,message = await doAlways(update,context)
    
    await message.reply_text("Scrivi ora il nome nel formato \"Cognome N.\" (Il bot non verifica la correttezza di questo, se sbagli non riceverai notifiche.)")
    return 1

async def setProf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Sarà eseguito sempre dopo impostaClasseConversation, non servirebbe fare doAlways, 
    # però meglio farlo così se qualcuno cambia nickname nel mentre il bot lo tiene in considerazione
    user,message = await doAlways(update,context)
    inpt = context.matches[0].group(1)
    
    change_prof(inpt, user.id) # Non serve controllo perché qua entra solo se è matchato
    
    await message.reply_text(f"Prof impostato a: {inpt}")
    return ConversationHandler.END

def change_prof(inpt, user):
    queryNoReturn("""--sql
        UPDATE utenti
        SET prof = ?, modalita = 'prof'
        WHERE id = ?;
    """,(inpt,user))
