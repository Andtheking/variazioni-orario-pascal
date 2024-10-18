from requirements import *

async def impostaClasse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    groups = context.match.groupdict()
    
    classe = groups['classe']
    u: Utente = Utente.get_by_id(update.effective_user.id)
    old_classe = u.classe
    
    u.classe = classe
    u.save()
    
    await rispondi(
        messaggio=message,
        text=f'Classe cambiata da {old_classe} a {classe} con successo.'
    )
    

    