from requirements import *

async def rimuoviClasse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.effective_message
    
    user_db: Utente = Utente.get_by_id(user_id)
    
    
    if user_db.classe:
        old_classe = user_db.classe
        user_db.classe = None
        user_db.save()
        await rispondi(message, text=f'Avevi impostato la classe {old_classe}. Ora non hai una classe.')
    else:
        await rispondi(message, text='Non hai una classe impostata.')
    
    