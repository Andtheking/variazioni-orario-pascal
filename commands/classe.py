from requirements import *

async def classe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.effective_message
    
    user_db: Utente = Utente.get_by_id(user_id)
    
    if user_db.classe:
        await rispondi(message, f'La tua classe al momento è: <code>{user_db.classe}</code>')
    else:
        await rispondi(message, f'Al momento non hai una classe impostata, puoi impostarla con /impostaClasse')