from requirements import *

async def impostaClasse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    groups = context.match.groupdict()
    
    classe = groups['classe']
    if classe is None:
        await rispondi(
            messaggio=message,
            text="Scrivi ora la classe che vuoi impostare (formato: 1A)"
        )
        return 1
    
    user_id = update.effective_user.id
    
    u: Utente = Utente.get_by_id(user_id)
    old_classe = u.classe
    
    u.classe = classe
    u.save()
    
    await rispondi(
        messaggio=message,
        text=f'Classe cambiata da {old_classe} a {classe} con successo.'
    )
    
    # TODO Mandare variazioni della nuova classe?
    return ConversationHandler.END