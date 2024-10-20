from requirements import *

# Questa funzione sarà eseguita prima di tutte le altre e per ogni messaggio che non è un comando
def middleware(next = None):
    async def doAlways(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != ChatType.PRIVATE and load_configs()['test']:
            if not update.effective_message.chat_id in load_configs()['enabled_groups']:
                await update.effective_message.chat.leave()
                return
        
        user = update.effective_user
        message = update.effective_message
        chat = message.chat
       
        if user is not None:
            db_user: Utente = Utente.select().where(Utente.id == user.id).first()
            if db_user is None:
                db_user = Utente.create(id = user.id, username = user.name)
                log(f"Inserito nel DB il seguente utente: {user.name} ({user.id})")
            
            if db_user.username != user.name:
                old_name = db_user.username
                db_user.username = user.name
                db_user.save()
                log(f"L'utente {old_name} ha cambiato nome: {user.name} ({user.id})")
        
        db_chat: Chat = Chat.select().where(Chat.id == chat.id).first()
        if db_chat is None:
            db_chat = Chat.create(id = chat.id, title = chat.effective_name)
            log(f"Inserita nel DB la seguente chat: {chat.effective_name} ({chat.id})")
        
        if db_chat.title != chat.effective_name:
            old_title = db_chat.title
            db_chat.title = chat.effective_name
            db_chat.save()
            log(f"La chat {old_title} ha cambiato titolo: {chat.effective_name} ({chat.id})")
        
        if next != None:
            return await next(update, context)
            
    return doAlways