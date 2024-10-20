from requirements import *

async def common(message, candidate):
    if candidate is None and message.reply_to_message is None:
        return
    
    if not Utente.get_by_id(message.from_user.id).admin:
        return
    
    if message.reply_to_message is not None:
        candidate_user = message.reply_to_message.from_user.id # ID
    else:
        candidate_user = candidate # Tipicamente username
    
    db_user: Utente = Utente.select().where((Utente.id == candidate_user) | (Utente.username == candidate_user)).get_or_none()
    
    if db_user is None:
        await rispondi(message, "Il bot non conosce l'utente in questione...")
        return
    
    return db_user

async def addAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    groups = context.match.groupdict()
    
    db_user: Utente = await common(message, groups['candidate'])

    if not db_user.admin:
        db_user.admin = True
        db_user.save()
        await rispondi(message, f"Aggiunto correttamente {db_user.username} come admin.")
        log(f"L'utente {db_user.username} è stato reso admin da {message.from_user.name}.", True)
    else:
        await rispondi(message, f"L'utente {db_user.username} è già admin.")
   
async def removeAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    groups = context.match.groupdict()
    
    db_user: Utente = await common(message, groups['candidate'])

    if db_user.admin:
        db_user.admin = False
        db_user.save()
        await rispondi(message, f"Rimosso correttamente {db_user.username} da admin.")
        log(f"L'utente {db_user.username} è stato rimosso dagli admin da {message.from_user.name}.", True)
    else:
        await rispondi(message, f"L'utente {db_user.username} non è admin.")